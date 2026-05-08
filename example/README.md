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
└── my_builtin_fs
    ├── CMakeLists.txt
    ├── fs.hpp
    ├── images
    │   ├── CMakeLists.txt
    │   ├── fs.hpp
    │   └── wall_small_jpg.cpp
    └── type_aliases.hpp

3 directories, 7 files
```

The outer `my_builtin_fs` contains no headers or sources. It serves to isolate
the include paths for the inner `my_builtin_fs` directory that contains all the
sources. The outer directory is added as an include directory to the targets
in the inner `my_builtin_fs`. So that the include paths are not poluted with
extra files.

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

The targets have the outer `my_builtin_fs` directory added as `PUBLIC`
by a `target_include_directories` call. So, the source of the `test` target
includes the headers as in `test.cpp`:
```cpp
// test.cpp
#include <iostream>
#include "my_builtin_fs/images/fs.hpp"

int main() {
  const my_builtin_fs::FileBuffer& a_file = my_builtin_fs::images::wall_small_jpg;

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
```

The files like `my_builtin_fs::images::wall_small_jpg` have `FileBuffer` type,
which is just an alias to `std::pair<unsigned char*, size_t>. See in the
generated `fs.hpp` headers:
```
// my_builtin_fs/my_builtin_fs/fs.hpp
#pragma once
#include "my_builtin_fs/type_aliases.hpp"

namespace my_builtin_fs {
namespace images {
extern const FileBuffer wall_small_jpg;
};
};

// my_builtin_fs/type_aliases.hpp
#pragma once
#include <cstddef>
#include <utility>

namespace my_builtin_fs {
using FileContentType = unsigned char;
using FileBuffer = std::pair<FileContentType* const, size_t>;
};
```

The used types `FileContentType` and `FileBuffer` are just aliases to
language-standard types, `unsigned char` and `std::pair` respectively.
It is nice that they are not custom types per a `builtin_fs` instance.
Potentially, you can make multiple `builtin_fs`, from separate TOML files,
and mix and match them, without declaration collisions on `FileBuffer` etc.

The file are declared as `const`, although that's not necessary. It seems
reasonable to make embedded files `const`, and pass `const` pointers to them.
Supporting mutable files would imply making correct containers around them,
so that the user has a clear and safe way to work with them. I don't need that
now. It may be something to add in future.

The underlying data is stored in standard types: `std::pair`, `unsigned char*`
and `size_t`. The namespaces only alias the `std::pair`. So, you can create
multiple `builtin_fs` instances, and the types will cooperate.

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
file size: 30482
contents byte: 255
```

The sizes of the binaries and the source file:
```
$ du -sh images/wall_small.jpg my_builtin_fs/my_builtin_fs/images/wall_small_jpg.cpp build/my_builtin_fs/my_builtin_fs/images/CMakeFiles/my_builtin_fs__images.dir/wall_small_jpg.cpp.o build/my_builtin_fs/my_builtin_fs/images/libmy_builtin_fs__images.a 
32K	images/wall_small.jpg
180K	my_builtin_fs/my_builtin_fs/images/wall_small_jpg.cpp
32K	build/my_builtin_fs/my_builtin_fs/images/CMakeFiles/my_builtin_fs__images.dir/wall_small_jpg.cpp.o
32K	build/my_builtin_fs/my_builtin_fs/images/libmy_builtin_fs__images.a
```
