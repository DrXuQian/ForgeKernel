"""Native PPU routing and portable knowledge, without a PPU device.

The extension test executes a real host CPython module through the frozen
adapter protocol. It does not claim to compile or execute a device kernel.
"""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from types import SimpleNamespace

import pytest

from forgekernel import launch, skills, taskcard
from forgekernel.localenv import load_machine
from forgekernel.loop import agent_policy, driver, lang_mode
from forgekernel.task import TaskError, load_task

from test_launch import _run_with_check, repo  # noqa: F401
from test_loop_driver import FakeBackend, _ctx
from test_task import _task

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "src/forgekernel/card_template/eval"
PPU = '[task]\nlanguage = "ppu"\narch = "ppu15"\n'
PPU_REF = PPU + '[reference]\nrun = "reference/run.py:run"\nsource = "reference"\n'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.mark.parametrize("arch", ["ppu10", "ppu15"])
def test_ppu_task_selects_its_native_mode(tmp_path, arch):
    task = load_task(_task(tmp_path, PPU.replace("ppu15", arch)))
    assert task.loop_language == "ppu"
    assert lang_mode.kb_root_name(task.loop_language) == "hw_kb/ppu"
    assert lang_mode.prompt_path(ROOT / "meta", "student_prompt.md", "ppu").parent.name == "ppu"
    assert lang_mode.language_problem("ppu", "kernel.cpp") is None
    assert lang_mode.language_problem("ppu", "kernel.py")
    assert lang_mode.owns_provenance("docs/kb-provenance/ppu/test.md", "ppu")
    assert not lang_mode.owns_provenance("docs/kb-provenance/ppu/test.md", "cutedsl")


@pytest.mark.parametrize("arch", ["sm90", "ppu17", "ZW890"])
def test_ppu_requires_a_supported_confirmed_arch(tmp_path, arch):
    with pytest.raises(TaskError, match="arch"):
        load_task(_task(tmp_path, PPU.replace("ppu15", arch)))


def test_builder_is_inside_task_and_native_only(tmp_path):
    for name, toml in (
        ("escape", PPU + '[ppu]\nbuild = "../outside.py"\n'),
        ("missing", PPU + '[ppu]\nbuild = "missing.py"\n'),
        ("python_kernel", PPU + '[ppu]\nbuild = "build.sh"\n'),
        ("cuda", '[task]\nlanguage="cuda"\narch="sm100"\n[ppu]\nbuild="build.py"\n'),
    ):
        with pytest.raises(TaskError):
            load_task(_task(tmp_path, toml, name=name))


def test_native_task_init(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "tasks/_template", tmp_path / "tasks/_template")
    monkeypatch.setattr(launch, "repo_root", lambda: tmp_path)
    with pytest.raises(SystemExit):
        launch.cmd_init(["norm", "--ppu"])
    assert not (tmp_path / "tasks/norm").exists()
    assert launch.cmd_init(["norm", "--ppu", "--arch", "ppu15"]) == 0
    task = load_task(tmp_path / "tasks/norm")
    assert task.language == "ppu" and task.arch == "ppu15"


@pytest.mark.parametrize("profile_available", [True, False])
def test_generated_card_and_sealed_reference_use_native_entry(repo, profile_available):
    run, task, check = _run_with_check(repo, PPU_REF)
    card = taskcard.write_card(run, task, check, load_machine(repo, environ={}))
    assert (card / "kernel.cpp").is_file()
    assert "hggc_runtime.h" in (card / "kernel.cpp").read_text()
    problem = json.loads((card / taskcard.PROBLEM).read_text())
    assert problem["ppu"] == {"arch": "ppu15"}
    taskcard.seal_reference(run, task, card)
    ref = run.operators_dir / taskcard.ref_tree(task.name)
    for tree in (card, ref):
        text = (tree / "gpu_entry.sh").read_text()
        subprocess.run(["bash", "-n", str(tree / "gpu_entry.sh")], check=True)
        assert "FK_PPU_ARCH" in text and "ppu_profile.py" in text
        assert all(word not in text for word in ("nvidia-smi", "/usr/local/cuda", "NCU_METRICS"))
        assert (tree / "eval/ppu_loader.py").is_file()
        submit = tomllib.loads((tree / "submit.toml").read_text())
        assert submit["env"]["FK_PPU_ARCH"] == "ppu15"
        assert "CUTE_DSL_ARCH" not in submit["env"]
        sdk = repo / "sdk"
        (sdk / "bin").mkdir(parents=True, exist_ok=True)
        (sdk / "bin/hgcc").write_text("#!/bin/sh\nexit 0\n")
        (sdk / "bin/hgcc").chmod(0o755)
        env = dict(os.environ, PPU_SDK=str(sdk))
        env.pop("PYTHONPATH", None)
        result = subprocess.run(["bash", str(tree / "gpu_entry.sh"), "cmd", "printf ppu-entry-ok"],
                                env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr + result.stdout
        assert "ppu-entry-ok" in result.stdout
    config = tomllib.loads(taskcard.write_loop_toml(
        run, task, card, deny=[], ncu=profile_available).read_text())["loop"]
    assert config["language"] == "ppu"
    assert config["profiler_backend"] == "acu"
    assert config["job_env_preflight"] == config["timeline_probe"] == "off"
    assert not config["stall_pricing"] and not config["orch_census"]
    if not profile_available:
        assert config["ncu_available"] is False


def test_task_builder_is_frozen_from_snapshot(repo):
    content = b"# task-owned native build adapter\n"
    run, task, check = _run_with_check(
        repo, PPU_REF + '[ppu]\nbuild = "build.py"\n', files={"build.py": content})
    card = taskcard.write_card(run, task, check, load_machine(repo, environ={}))
    assert (card / "eval/ppu_build.py").read_bytes() == content
    assert task.ppu_builder.is_relative_to(run.task_dir)


def test_ppu_does_not_seed_or_run_nvidia_instruments(tmp_path):
    be = FakeBackend([], [])
    ctx = replace(_ctx(tmp_path, be), language="ppu", kernel_file="kernel.cpp",
                  kb_arch="ppu15", timeline_probe="on", stall_pricing=True,
                  orch_census=True, recon_dir=tmp_path / "recon")
    assert not ctx.stall_pricing and not ctx.orch_census
    assert not driver._timeline_on(ctx)
    assert driver._ncu_mode(ctx) == "acu"
    driver._seed_sass_tools(ctx, be)
    driver._ensure_ref_pricing(ctx)
    assert driver.job_env_preflight(ctx) is None
    assert not be.calls
    assert not (ctx.recon_dir / "notes/sass_tools.py").exists()


def test_native_evidence_gate_accepts_owned_unavailability(tmp_path):
    be = FakeBackend([], [])
    ctx = replace(_ctx(tmp_path, be), language="ppu", recon_dir=tmp_path,
                  recon_path=tmp_path / "report.md")
    missing = driver._missing_recon_evidence(ctx, False, False, False)
    assert missing == ["ACU", "NATIVE-ISA"]
    msg = driver._evidence_gate_msg(missing, ctx=ctx)
    assert "ACU-EVIDENCE:" in msg and "sass_tools" not in msg
    ctx.recon_path.write_text(
        "ACU-EVIDENCE: job 12345; duration only; tensor metrics unavailable.\n"
        "NATIVE-ISA-EVIDENCE: unavailable; native disassembler absent; resources unmeasured.\n")
    assert not driver._missing_recon_evidence(ctx, False, False, False)
    assert driver._sass_evidence(ctx, False)


def test_history_is_teacher_only_and_removed_on_role_change(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    policy = agent_policy.from_config(
        {"loop": {"language": "ppu", "ref_source_paths": [], "ref_source_urls": []}},
        oracle_mode="source", repo_root=ROOT, teacher_trees=[], language="ppu")
    policy.install("teacher", ws)
    mirrored = ws / skills.MIRROR_RELPATH
    assert all((mirrored / name / "SKILL.md").is_file()
               for name in skills.OPERATOR_HISTORY_SKILLS)
    assert "before reconnaissance" in policy.notice("teacher")
    for role, restricted in (("student", policy),
                             ("teacher", replace(policy, oracle_mode="blackbox"))):
        restricted.install(role, ws)
        assert all(not (mirrored / name).exists() for name in skills.OPERATOR_HISTORY_SKILLS)
        deny = restricted.settings(role, ws)["sandbox"]["filesystem"]["denyRead"]
        assert all(str(p.resolve()) in deny for p in skills.history_dirs())


def test_ppu_header_declaration_must_be_a_list():
    problems = agent_policy.declaration_problems(
        {"loop": {"ppu_source_dirs": "/sdk/include"}}, "source")
    assert any("ppu_source_dirs must be a list" in p for p in problems)


def test_bootstrap_history_does_not_expose_reference_or_keys(tmp_path):
    reference = tmp_path / "reference"
    secret = tmp_path / "key"
    policy = agent_policy.AgentPolicy(
        oracle_mode="source", repo_root=ROOT, language="ppu",
        ref_source_paths=(reference,), secret_files=(secret,),
        ppu_bootstrap_history=True)
    assert policy.history_allowed("student")
    assert {reference, secret} <= set(policy.deny_read("student"))
    assert not replace(policy, oracle_mode="blackbox").history_allowed("student")
    assert not replace(policy, ppu_bootstrap_history=False).history_allowed("student")


def test_native_milestone_survives_resume_without_nvidia_counters(tmp_path):
    from forgekernel.milestone import validate_milestone
    from forgekernel.loop.cli import _milestone_valid, _will_distill
    from test_milestone import VALID
    text = VALID.replace("[SYNC: none]", "[SYNC: native-barrier]").replace(
        "[GATHER: none]", "[GATHER: serial]").replace(
        "- Mechanism-verification line: tensor pipe active % vs the ref baseline ≥80%",
        "- Mechanism-verification line: [VERIFY: correctness] sync: all handoffs checked\n"
        "- [VERIFY: acu-direct] gather: native issue counter agrees with the measured budget")
    assert validate_milestone(text, language="ppu") == []
    assert validate_milestone(text)  # native channels cannot change NVIDIA semantics
    missing = text.replace("[VERIFY: correctness] sync:", "[VERIFY: ncu-direct] sync:")
    assert any("PPU sync needs" in p for p in validate_milestone(missing, language="ppu"))
    path = tmp_path / "m.md"
    path.write_text(text)
    assert _milestone_valid(path, "ppu")
    assert not _will_distill(path, "oracle", language="ppu")


def test_fresh_recon_is_compared_with_prior_files_despite_clock_skew(tmp_path):
    from test_loop_driver import FakeBackend
    ctx = replace(_ctx(tmp_path, FakeBackend([], [])), language="ppu",
                  recon_dir=tmp_path, recon_path=tmp_path / "report.md")
    paths = [ctx.recon_path, tmp_path / "candidates.md"]
    for path in paths:
        path.write_text("prior operator")
    start = 1e18  # wall clock ahead of every filesystem timestamp
    ctx._recon_freshness = (start, {str(p): driver._recon_file_version(p) for p in paths})
    assert not driver._recon_artifacts_written(ctx, start)
    paths[0].write_text("current report")
    assert not driver._recon_artifacts_written(ctx, start)  # both must change
    paths[1].write_text("current candidates")
    assert driver._recon_artifacts_written(ctx, start)


def test_native_compiler_command_never_uses_nvidia(tmp_path):
    build = module(EVAL / "ppu_build.py", "test_ppu_build")
    for arch, target in (("ppu10", "ppu_10"), ("ppu15", "ppu_15")):
        cmd = build.build_command(
            tmp_path / "kernel.cpp", tmp_path / "kernel.so", "native_kernel", arch,
            sdk=tmp_path / "sdk", torch_root=tmp_path / "torch",
            python_include="/python/include", abi=1, actlize=tmp_path / "actlize")
        assert cmd[:4] == [str(tmp_path / "sdk/bin/hgcc"), "-x", "hg", f"-arch={target}"]
        assert "-DSWITCH_TO_HGGCRT" in cmd
        assert str(tmp_path / "actlize/include") in cmd
        assert not any("nvcc" in a or "sm_90" in a for a in cmd)
    with pytest.raises(ValueError, match="unsupported PPU"):
        build.build_command(Path("k.cpp"), Path("k.so"), "k", "sm90",
                            sdk=tmp_path, torch_root=tmp_path, python_include="/i", abi=0)


def test_native_loader_builds_loads_and_invalidates_source_on_host(tmp_path, monkeypatch):
    if shutil.which("cc") is None:
        pytest.skip("host C compiler needed for the real extension protocol test")
    shutil.copy2(EVAL / "ppu_loader.py", tmp_path / "ppu_loader.py")
    # A task adapter can use its installed native build. This fixture deliberately
    # builds only a host module to exercise loading without pretending it is PPU.
    (tmp_path / "ppu_build.py").write_text(
        "import argparse, subprocess, sysconfig\n"
        "p=argparse.ArgumentParser()\n"
        "for k in ('source', 'output', 'module', 'arch'): p.add_argument('--'+k)\n"
        "a=p.parse_args()\n"
        "assert a.arch in ('ppu10','ppu15')\n"
        "subprocess.run(['cc','-x','c','-shared','-fPIC',"
        "'-I'+sysconfig.get_paths()['include'],'-DMODULE='+a.module,"
        "a.source,'-o',a.output],check=True)\n")
    source = tmp_path / "kernel.cpp"
    code = r"""
#include <Python.h>
#define JOIN_(a,b) a##b
#define JOIN(a,b) JOIN_(a,b)
static PyObject* run(PyObject* self, PyObject* args) { return PyLong_FromLong(41); }
static PyMethodDef methods[] = {{"run",run,METH_NOARGS,"host fixture"},{NULL,NULL,0,NULL}};
static struct PyModuleDef def = {PyModuleDef_HEAD_INIT,"fixture",NULL,-1,methods};
PyMODINIT_FUNC JOIN(PyInit_,MODULE)(void) { return PyModule_Create(&def); }
"""
    source.write_text(code)
    monkeypatch.setenv("FK_KERNEL_BUILD_DIR", str(tmp_path / "build"))
    loader = module(tmp_path / "ppu_loader.py", "test_ppu_loader")
    fn = loader.load_ppu_entry(source, "run", {"arch": "ppu15"})
    assert fn() == 41
    assert loader.load_ppu_entry(source, "run", {"arch": "ppu15"}) is fn
    source.write_text(code.replace("41", "42"))
    assert loader.load_ppu_entry(source, "run", {"arch": "ppu15"})() == 42
    manifests = list((tmp_path / "build").glob("*/manifest.json"))
    assert len(manifests) == 2
    assert all(json.loads(p.read_text())["arch"] == "ppu15" for p in manifests)
    with pytest.raises(AttributeError, match="exports no callable"):
        loader.load_ppu_entry(source, "absent", {"arch": "ppu15"})
    with pytest.raises(ValueError, match="supported native target"):
        loader.load_ppu_entry(source, "run", {"arch": "sm90"})


def test_native_loader_rejects_a_builder_that_produces_nothing(tmp_path, monkeypatch):
    shutil.copy2(EVAL / "ppu_loader.py", tmp_path / "ppu_loader.py")
    (tmp_path / "ppu_build.py").write_text("print('no binary')\n")
    source = tmp_path / "kernel.cpp"
    source.write_text("// fixture")
    monkeypatch.setenv("FK_KERNEL_BUILD_DIR", str(tmp_path / "build"))
    loader = module(tmp_path / "ppu_loader.py", "test_ppu_loader_failure")
    with pytest.raises(RuntimeError, match="PPU build failed"):
        loader.load_ppu_entry(source, "run", {"arch": "ppu15"})


def test_profile_invokes_native_acu_and_retains_requested_metrics(tmp_path, monkeypatch, capsys):
    profile = module(EVAL / "ppu_profile.py", "test_ppu_profile")
    calls = []
    monkeypatch.setenv("FK_ACU", "/sdk/bin/acu")
    monkeypatch.setenv("FK_ACU_METRICS", "tensor__native.sum,ppu__time_duration.sum")
    monkeypatch.setattr(profile.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd) or SimpleNamespace(returncode=0))
    monkeypatch.setattr(sys, "argv", ["ppu_profile", "--launch-count", "7"])
    assert profile.main() == 0
    cmd = calls[0]
    assert cmd[0] == "/sdk/bin/acu" and cmd[-1] == "eval/ncu_run.py"
    assert cmd[cmd.index("--metrics") + 1] == "ppu__time_duration.sum,tensor__native.sum"
    assert cmd[cmd.index("--profile-from-start") + 1] == "off"
    assert "FORGE_PPU_ACU_CSV" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["ppu_profile"])
    assert profile.main() == 0
    assert "--launch-count" not in calls[-1]  # never truncate the automatic profile window
    assert calls[-1][calls[-1].index("--page") + 1] == "raw"
