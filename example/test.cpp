#include <iostream>
#include "my_builtin_fs/images/fs.hpp"

int main() {
  auto& a_file = my_builtin_fs::images::wall_small_jpg;
  std::cout << "file size: " << a_file.n_bytes << "\n";
  std::cout << "contents byte: " << (unsigned) a_file.data[0] << "\n";
}
