A couple scripts to embed arbitrary files into C++ binaries.

The goal is to build CMake C++ projects that use random asset files as:
```cpp
FileBuffer& img = builtin_fs::image::my_image_jpg;

// where the types are
using FileContentType = unsigned char;
struct FileBuffer {
    FileContentType* const data;
    size_t n_bytes;
};
```

So that the file is available in memory.
For example, STB image library can load it:
```cpp
int width, height, n_channels;
unsigned char *image_data =
  stbi_load_from_memory(img.data, img.n_bytes, &width, &height, &n_channels, 0);
```

It is handy in Emscripten WASM builds for Web.

A demo example is in `example/`.
