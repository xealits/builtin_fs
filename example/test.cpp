#include <iostream>
#include "my_builtin_fs/images/fs.hpp"

int main() {
  auto& a_file = my_builtin_fs::images::wall_small_jpg;

  {
    // structured binding
    auto [data, n_bytes] = a_file;
    std::cout << "file size: " << n_bytes << "\n";
    std::cout << "contents byte: " << (unsigned) data[0] << "\n";
  }

  {
    // but I don't like that the user has no handle to ensure the types
    auto* data = a_file.first;
    //size_t n_bytes = a_file.first;
    size_t n_bytes = a_file.second;
    std::cout << "file size: " << n_bytes << "\n";
    std::cout << "contents byte: " << (unsigned) data[0] << "\n";
  }
}
