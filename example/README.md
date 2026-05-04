Let's embed the files in `images/` and access them in `test.cpp`.
The python script sets up a standalone `builtin_fs` subdirectory:
```
python ../files_to_builtin.py ./.builtin_fs.toml --builtin-fs my_builtin_fs
```

The TOML file defines glob patterns for the files to grab:
```
$ cat ./.builtin_fs.toml 
[images]
glob = ["*.jpg"]
```

The resulting directory is a CMake subdirectory:
```
$ tree my_builtin_fs/
my_builtin_fs/
├── CMakeLists.txt
├── FileBuffer.hpp
├── fs.hpp
└── images
    ├── CMakeLists.txt
    ├── fs.hpp
    └── wall_small_jpg.cpp

2 directories, 6 files
```

The CMake projects uses its targets as in `CMakeLists.txt`:
```cmake
# CMakeLists.txt
cmake_minimum_required (VERSION 3.23)

project(builtin_fs_example ...)
...

add_subdirectory(my_builtin_fs)

add_executable(test test.cpp)
target_link_libraries(test PUBLIC my_builtin_fs__images)
```

It creates an `OBJECT` lib target for each file, and a `STATIC` for file groups.
Each subdirectory has a corresponding `STATIC` library that includes the object
files from the directory and all its descendants.

The targets have the root directory of the `builtin_fs` added as `PUBLIC`
by a `target_include_directories` call, and the parent of the root directory is
added as well. So, the source of the `test` target includes the headers as in
`test.cpp`:
```cpp
// test.cpp
#include <iostream>
#include "my_builtin_fs/images/fs.hpp"

int main() {
  auto& a_file = my_builtin_fs::images::wall_small_jpg;
  std::cout << "file size: " << a_file.n_bytes << "\n";
  std::cout << "contents byte: " << (unsigned) a_file.data[0] << "\n";
}
```

Something to cleanup for the case of several directories, the include paths
also find these:
```
#include "images/fs.hpp"
#include "fs.hpp"
#include "FileBuffer.hpp"
```

CMake builds it as usual:
```
$ cmake -S . -B build
...
$ cmake --build build
[ 25%] Building CXX object my_builtin_fs/images/CMakeFiles/my_builtin_fs__images.dir/wall_small_jpg.cpp.o
[ 50%] Linking CXX static library libmy_builtin_fs__images.a
[ 50%] Built target my_builtin_fs__images
[ 75%] Building CXX object CMakeFiles/test.dir/test.cpp.o
[100%] Linking CXX executable test
[100%] Built target test
$ ./build/test
file size: 30482
contents byte: 255
```

The sizes of binaries and the source file:
```
$ du -sh images/wall_small.jpg my_builtin_fs/images/wall_small_jpg.cpp build/my_builtin_fs/images/libmy_builtin_fs__images.a build/my_builtin_fs/images/CMakeFiles/my_builtin_fs__images.dir/wall_small_jpg.cpp.o
32K	images/wall_small.jpg
180K	my_builtin_fs/images/wall_small_jpg.cpp
32K	build/my_builtin_fs/images/libmy_builtin_fs__images.a
32K	build/my_builtin_fs/images/CMakeFiles/my_builtin_fs__images.dir/wall_small_jpg.cpp.o
```
