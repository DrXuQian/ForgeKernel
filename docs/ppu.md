# 在 PPU 上运行 ForgeKernel

PPU 适配沿用 ForgeKernel 的 task → judge → reference 校准 → recon/candidates →
M0 → student → 正确性/计时 → teacher 修订 → 知识认证流程。
学生写原生 C++，由 HGCC 编译；张量、stream 和 event 使用设备配套 PyTorch 的
CUDA 兼容接口。现有 NVIDIA CUDA/CuTe DSL 模式继续使用自己的工具和知识库。

## 已接入的范围

| 项目 | PPU 路径 |
|---|---|
| 任务 | `language = "ppu"`，`arch = "ppu10"` 或 `"ppu15"` |
| 编译 | `hgcc -x hg -arch=ppu_10` / `ppu_15`；可选任务内构建适配器 |
| 学生交付 | `kernel.cpp`，单文件 PyTorch/PyBind 扩展 |
| 性能证据 | 原生 ACU CSV，保留指标原名、单位和逐 launch 数据 |
| 经验检索 | source teacher 和首次 reference 生成按需读取两个 PPU skill |
| 知识认证 | `hw_kb/ppu/<arch>/`，只接收实际目标上的 probe 证据 |

PPU1.7 的迁移经验保留在知识包中，但本版本尚未提供其原生任务 target。
不能把 NVIDIA `sm90` 当作 PPU1.7 的构建参数。现有
`scripts/self_evolve.py` 的自动跨 generation 演进是 CuTe DSL 流程，尚未适配 PPU。
PPU 可以使用正常的 `forge new/run` 优化流程和中断续跑。

## 准备实际机器

运行 ForgeKernel 的环境需要 Python ≥ 3.11、git 和原项目要求的 Claude Code CLI；
无 reference 时，其自动生成流程还需要 tmux。
执行 kernel 的环境需要匹配设备的 PPU 驱动、SDK、PyTorch、Python 开发头文件和
本机 C++ 编译器；ACU/Asys 也应来自该 SDK。不要用普通 NVIDIA PyTorch 替代厂商
的 PPU PyTorch。安装 ForgeKernel 时保留现有配套 PyTorch，例如在已配置的环境中：

```bash
python3 -m pip install -e .
cp local.env.example local.env
```

`local.env` 配置本机执行：

```dotenv
FK_DELIVERY=local
FK_GPU=0
PPU_SDK=/path/to/installed/ppu-sdk
# 使用 actlize 的任务才需要；来自官方版本，并记录实际 revision。
PPU_ACTLIZE_DIR=/path/to/official/actlize
```

激活厂商提供的运行环境，确保任务进程的 `python3`、runtime 动态库路径与
PyTorch 匹配。HGCC 的默认适配器读取上述 SDK 和 actlize 路径，不猜测安装目录。
官方依赖入口见 [sources](../skills/ppu-kernel-knowledge/references/sources.md#official-upstreams)。
这些路径属于当前机器配置，不应写进可移植的知识包。

先在目标机器执行环境查询（脚本直接读取环境变量，不自动 source `local.env`）：

```bash
python3 scripts/inspect_ppu.py --sdk /path/to/installed/ppu-sdk \
  --device 0 --out /tmp/forge-ppu-inspect-01
```

查看生成的 `environment.json`、设备属性和各工具日志。输出目录必须是新的。
查询成功只证明 runtime/设备可访问，不能代替 kernel 的原生编译、正确性和计时。
公开 M890 对应 PPU1.5、原生 `ppu0015`/`ppu_15`；本地叫 ZW890 的机器仍需核对
实际身份。810/PPU1.0 也按实机确认，不按 CUDA compute capability 推断 PPU 代际。

远程执行使用原项目的 `FK_DELIVERY=ssh`、`REMOTE_HOST`、
`REMOTE_WORKDIR`、`REMOTE_ENV_FILE`。把 SDK/runtime/PyTorch 激活写进远端
env file。离线 agent 所需的 SDK/actlize 头文件也要在 agent 主机可读；本机有效的
`PPU_SDK/include`、`PPU_ACTLIZE_DIR/include` 会进入运行配置的 `ppu_source_dirs`。

## 创建和运行任务

确认是 PPU1.5 后，例如优化 dense FlashAttention：

```bash
forge init fa_dense --ppu --arch ppu15
```

按原 task 格式填写 `tasks/fa_dense/description.md` 与 `shapes.json`：
精确的 B/Hq/Hkv/Sq/Sk/D、dtype、layout、mask/causal、误差准则和计时边界。
性能目标仍以正确 kernel 的完整调用计时判断，tensor 利用率是诊断证据。
仅优化某些 dense shape 时，把这些 shape 明确写进任务。

已有实现时，把可在 PPU 上运行的 reference wrapper 和所需源码放在任务内：

```toml
[task]
language = "ppu"
arch = "ppu15"

[reference]
run = "reference/run.py:run"
source = "reference"

[target]
ratio = 1.1
timing = "device"
```

`run` 的输入/输出与任务一致；校准和计时实际调用它。适配 NVIDIA 算子时，
可先用设备支持的 PyTorch reference 建立正确性与目标机基线，把原 NVIDIA 源码和
迁移说明一并放到 teacher 可读的 reference 目录，明确哪个 wrapper 被计时。
NVIDIA 机器上的历史时间不能作为 PPU 实测基线。不给 reference 时，ForgeKernel
先用同一原生构建和 evaluator 生成、测量并验收一个 reference，再开始正常流程。

```bash
forge new tasks/fa_dense --dry-run
forge new tasks/fa_dense
# 使用上一条返回的真实 run 路径：
forge run .artifacts/fa_dense_<id>
forge status .artifacts/fa_dense_<id>
```

dry-run 检查任务配置，不调用 PPU。第一次实机运行需要确认扩展成功构建、reference
与 judge 一致、候选数值通过，再讨论性能。

## 使用已有构建系统

默认构建器将 `kernel.cpp` 作为单个原生 HGCC PyTorch 扩展编译；定义
`PYBIND11_MODULE(TORCH_EXTENSION_NAME, m)` 并导出 `run`。
它不适合直接承载一个完整第三方多文件工程。已有 SDK 工程需要不同参数时，在任务内
提供一个自包含 `build.py`：

```toml
[ppu]
build = "build.py"
```

适配器接口：

```text
python3 build.py --source <staged-kernel.cpp> --output <extension.so> \
  --module <unique-module-name> --arch ppu10|ppu15
```

适配器必须使用当前 SDK 编译指定源码，以给定 module 名导出 PyBind 模块，并写出
指定 `.so`；错误返回非零。它应包含所需构建逻辑，依赖来自已安装的公共 SDK/库，
不能返回已有 operator 的二进制。任务快照将适配器冻结到 evaluator，学生只改 kernel。
每个 job 重新构建，进程内按源码/适配器内容复用；构建目录保留日志和 manifest。

## ACU、Asys 与优化经验

`forge run` 先探测 ACU。自动采集默认只请求 `ppu__time_duration.sum`，
足够识别热 kernel，不足以说明 tensor 利用率。teacher 应先读取
[PPU profiling](../skills/ppu-profiling/SKILL.md)，查询安装版本/目标支持的指标和含义，
再通过 probe 或机器配置 `FK_ACU_METRICS` 请求精确指标列表
（逗号分隔，自动补入 duration）。`FK_ACU` 可指定 ACU 路径。

ACU 的 time 只在单位已知时转为 ns；热 kernel 的其他指标保留原名、单位和每次 launch 的数值，
进入迭代记录与 teacher 视图。不会把它们映射成 NVIDIA tensor 百分比或套 SM90 阈值。
调用失败、duration 缺失或单位未知时明确无证据，仍可进行独立的正确性和干净计时。
自动采集覆盖限定的 profiler window，不设置固定 launch 上限。手动设置上限时核对
采集 launch 数，不要用截断窗口估算完整算子耗时。
自动采集使用 PyTorch profiler start/stop 兼容接口；该 SDK 不支持时改用
teacher 的原生范围采集 probe，并记录缺失的自动通道。

Asys 用于定位 launch gap、复制和同步，通过原有 `RECON_REQUEST`/
`PROBE_REQUEST` job 通道采集。ACU/Asys MCP 可以使用，但不是必须依赖。
原版 NVIDIA SASS、stall pricing、orchestration census 和 timeline 自动插桩在
PPU 模式关闭；需要时写 native probe，不生成假的 NVIDIA verdict。
recon 必须记录 `ACU-EVIDENCE:` 和 `NATIVE-ISA-EVIDENCE:` 的测量范围，
或写明 unavailable、原因和未解决问题。

source teacher 在初次 recon/M0 前，从
[PPU knowledge](../skills/ppu-kernel-knowledge/SKILL.md) 按架构、FA/linear attention、
量化、数值、访存等问题查找历史经验。首次 reference 生成也可读取这些经验；
之后的 student 只读 teacher 接受的 milestone 与认证知识。teacher 在新 profile、
数值失败或回归后重新检索，记录来源、原目标、当前适用性及验证实验。
这两包资料和必要 Markdown 都在仓库内，不依赖个人 repo、memory 或全局 skills。

初始 `hw_kb/ppu` 没有宣称已通过 PPU 实机认证的 recipe。新增知识必须在实际目标
执行 probe，并保存 SDK、设备、源码和测量证据。

## 验证边界

本适配的测试覆盖任务/配置、reference 封装、原生构建命令、扩展加载协议、
ACU 多 launch/单位解析和 agent 的知识边界。host 扩展测试只验证加载协议。
没有 PPU 实机的环境不能证明 810/890 上的编译链接、数值精度或性能；
这些必须由上述目标任务的实际运行给出。
