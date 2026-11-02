// SPDX-License-Identifier: Apache-2.0
// Query the selected PPU runtime device; this program launches no kernels.
#include <hggc_runtime.h>

#include <cstdlib>
#include <iomanip>
#include <iostream>

bool check(hggcError_t status, char const* operation) {
  if (status == hggcSuccess) return true;
  std::cerr << operation << ": " << hggcGetErrorString(status) << '\n';
  return false;
}

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  char* end = nullptr;
  long selected = std::strtol(argv[1], &end, 10);
  if (!end || *end || selected < 0) return 2;
  int count = 0;
  if (!check(hggcGetDeviceCount(&count), "hggcGetDeviceCount")) return 1;
  if (selected >= count) {
    std::cerr << "Requested device " << selected << "; visible count " << count << '\n';
    return 1;
  }
  hggcDeviceProp p{};
  if (!check(hggcGetDeviceProperties(&p, static_cast<int>(selected)),
             "hggcGetDeviceProperties")) return 1;

  std::cout << "FORGE_PPU_DEVICE_JSON={"
    << "\"name\":" << std::quoted(p.name)
    << ",\"ordinal\":" << selected
    << ",\"visible_devices\":" << count
    << ",\"compute_capability_major\":" << p.major
    << ",\"compute_capability_minor\":" << p.minor
    << ",\"compute_units\":" << p.multiProcessorCount
    << ",\"warp_size\":" << p.warpSize
    << ",\"global_memory_bytes\":" << p.totalGlobalMem
    << ",\"shared_per_cu_bytes\":" << p.sharedMemPerMultiprocessor
    << ",\"shared_per_block_bytes\":" << p.sharedMemPerBlock
    << ",\"shared_per_block_optin_bytes\":" << p.sharedMemPerBlockOptin
    << ",\"registers_per_cu\":" << p.regsPerMultiprocessor
    << ",\"registers_per_block\":" << p.regsPerBlock
    << ",\"max_threads_per_cu\":" << p.maxThreadsPerMultiProcessor
    << ",\"max_threads_per_block\":" << p.maxThreadsPerBlock
    << ",\"max_blocks_per_cu\":" << p.maxBlocksPerMultiProcessor
    << ",\"l2_cache_bytes\":" << p.l2CacheSize
    << ",\"memory_bus_width_bits\":" << p.memoryBusWidth
    << ",\"pci_domain\":" << p.pciDomainID
    << ",\"pci_bus\":" << p.pciBusID
    << ",\"pci_device\":" << p.pciDeviceID
    << "}\n";
  return 0;
}
