import argparse
from collections import defaultdict
from glob import glob
import logging
import os
from os.path import getmtime
from pathlib import Path
from pprint import pprint
import tomllib


cmakelists_root = """# top-level CMakeLists.txt with the builtin_fs functions

get_filename_component(ROOT_DIR_NAME ${CMAKE_CURRENT_SOURCE_DIR} NAME)
message(STATUS "${PROJECT_NAME} > builtin_fs root dir name is ${ROOT_DIR_NAME}")
#option(ROOT_NAMESPACE_NAME "set the name of the builtin_fs root namespace" ${ROOT_DIR_NAME})
set(ROOT_NAMESPACE_NAME ${ROOT_DIR_NAME})
message(STATUS "${ROOT_DIR_NAME} > configured root namespace name ${ROOT_NAMESPACE_NAME}")

# add_compile_definitions(BUILTIN_FS_ROOT_NAME=${ROOT_NAMESPACE_NAME})

#set(PROJECT_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR})
cmake_path(GET CMAKE_CURRENT_SOURCE_DIR PARENT_PATH PROJECT_INCLUDE_DIRS)
list(APPEND PROJECT_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR})
message(STATUS "${ROOT_DIR_NAME} > include dir ${PROJECT_INCLUDE_DIRS}")

set(CURRENT_FS_DIR_PATH "${ROOT_NAMESPACE_NAME}")
set(NESTING_LEVEL 0)

function(set_current_fs_dir_path)
  # nested sibdir names are used in the target names
  get_filename_component(subdir_name ${CMAKE_CURRENT_SOURCE_DIR} NAME)
  set(CURRENT_FS_DIR_PATH "${CURRENT_FS_DIR_PATH}__${subdir_name}" PARENT_SCOPE)
endfunction()

function(create_static_libs_from_cpp) # DIR_PATH CURRENT_FS_DIR_PATH)
  string(REPEAT "  " ${NESTING_LEVEL} nesting_spaces)
  message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> getting targets in ${CMAKE_CURRENT_SOURCE_DIR}")

  file(GLOB cpp_files RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.cpp")
  set(sublib_sources "")

  foreach(cpp_file ${cpp_files})
    if(${cpp_file} STREQUAL "test.cpp")
      message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> skipping test.cpp")
      continue()
    endif()

    # name without extension (WE)
    get_filename_component(filename_we ${cpp_file} NAME_WE)
    set(target_name "${CURRENT_FS_DIR_PATH}__${filename_we}")

    # BUILTIN FS object lib for the file contents
    add_library(${target_name} OBJECT ${cpp_file})
    target_include_directories(${target_name} PUBLIC ${PROJECT_INCLUDE_DIRS})
    set_target_properties(${target_name} PROPERTIES EXCLUDE_FROM_ALL TRUE)
    list(APPEND sublib_sources ${cpp_file})

    message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> added a builtin FS target ${target_name}")
  endforeach()

  # add possible targets in sub-directories
  file(GLOB SUBDIRS LIST_DIRECTORIES true RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/*)
  message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> looking at subdirs in ${CMAKE_CURRENT_SOURCE_DIR}")
  foreach(subdir_name ${SUBDIRS})
    set(subdir_path ${CMAKE_CURRENT_SOURCE_DIR}/${subdir_name})

    if(NOT IS_DIRECTORY ${subdir_path})
      continue()
    endif()

    if(NOT EXISTS "${subdir_path}/CMakeLists.txt")
      continue()
    endif()

    message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> looking at ${subdir_path}")
    add_subdirectory(${subdir_path})

    # check if a target was added
    get_filename_component(subdir_name ${subdir_path} NAME)
    set(subdir_target_name ${CURRENT_FS_DIR_PATH}__${subdir_name})
    if(TARGET ${subdir_target_name})
      message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> adding targets objects from ${subdir_target_name}")

      get_target_property(SUBDIR_SOURCES ${subdir_target_name} SOURCES)
      foreach(SOURCE ${SUBDIR_SOURCES})
        list(APPEND sublib_sources "${subdir_path}/${SOURCE}")
      endforeach()
    endif()
  endforeach()

  # BUILTIN FS static lib for a directory tree (directory and subdirectories)
  add_library(${CURRENT_FS_DIR_PATH} STATIC ${sublib_sources})
  target_include_directories(${CURRENT_FS_DIR_PATH} PUBLIC ${PROJECT_INCLUDE_DIRS})
  set_target_properties(${CURRENT_FS_DIR_PATH} PROPERTIES EXCLUDE_FROM_ALL TRUE)
  message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> added a builtin FS STATIC library ${CURRENT_FS_DIR_PATH} out of all subdir sources")

endfunction()

create_static_libs_from_cpp()
"""

cmakelists_subdir = """set_current_fs_dir_path()
math(EXPR NESTING_LEVEL "${NESTING_LEVEL} + 1")
string(REPEAT "  " ${NESTING_LEVEL} nesting_spaces)
message(STATUS "${ROOT_DIR_NAME} ${nesting_spaces}> set ${CURRENT_FS_DIR_PATH}")

create_static_libs_from_cpp(${NESTING_LEVEL})
"""

builtin_fs_include_type_aliases = """#pragma once
#include <cstddef>
#include <utility>

namespace {root_name} {{
using FileContentType = unsigned char;
using FileBuffer = std::pair<FileContentType* const, size_t>;
}};
"""

def load_builtin_fs_toml(directory, toml_file):
    toml_path = Path(directory) / toml_file
    if not toml_path.exists():
        raise FileNotFoundError(f"{toml_file} not found in {directory}")

    with open(toml_path, "rb") as f:
        return tomllib.load(f)

def path_list_to_nested_dict(paths: list):
    """
    Convert a list of PosixPath to a dict according to the directory nestings.
    """

def match_config(sources_directory: Path, files_config: dict):
    matches = []

    # match the glob patterns
    direct_globs = files_config.get("glob")
    if direct_globs is not None:
        direct_matches = []
        for pattern in direct_globs:
            direct_matches += glob(pattern, root_dir=sources_directory)

        matches += [sources_directory / fpath for fpath in direct_matches]

    # treat other entries as patterns for subdirectories
    for subdir_name, subdir_config in files_config.items():
        if subdir_name in ["glob"]:
            continue

        subdir_path = sources_directory / subdir_name
        matches += match_config(subdir_path, subdir_config)

    return matches

def append_file_to_nested_dict(nested_dict: dict, filename: Path):
    """append_file_to_nested_dict(nested_dict: dict, filename: Path)

    The nested_dict structure:
    * the "." item contains a set with the filenames in this directory
    * in other items, the key is a subdirectory name, the value is a dictionary of its contents
    """

    parts = filename.parts
    assert len(parts) > 0

    # create sub-dictionaries if needed
    cur_nested_level = nested_dict
    for subdir in parts[:-1]:
        cur_nested_level = nested_dict.setdefault(subdir, {".": set()})

    # add the full file path as the leaf
    cur_nested_level.setdefault(".", set()).add(filename)

def sources_to_nested_dict(source_paths: list):
    nested_dict = {".": set()}
    for path in source_paths:
        if path.is_dir():
            logging.warning(f"skipping a directory in the matched sources list {path}")
            continue

        append_file_to_nested_dict(nested_dict, path)

    return nested_dict

def builtin_file_suffix(fname: Path, new_extension: str = None):
    assert isinstance(fname, Path)

    stem = fname.stem
    suffix = fname.suffix[1:]
    new_name = f"{stem}_{suffix}"

    if new_extension is not None:
        new_name += new_extension

    # TODO: I probably should just return it with .name - that's how it is used everywhere
    return fname.with_name(new_name)

def builtin_file_declaration(fpaths: list, nesting_dirs: list = []):
    assert all(isinstance(fp, Path) for fp in fpaths)

    declarations = []
    for fname in fpaths:
        decl_name = builtin_file_suffix(fname).name
        decl = f"extern const FileBuffer {decl_name};"
        declarations.append(decl)

    if not declarations:
        return []

    declarations_str = "\n".join(declarations)
    for name in nesting_dirs:
        declarations_str = f"namespace {name} {{\n{declarations_str}\n}};"

    return [declarations_str]

template_definition_file = """#include "{root_name}/type_aliases.hpp"

static {root_name}::FileContentType content_[] = {{
{content}
}};
static constexpr size_t file_size_ = sizeof(content_) / sizeof(content_[0]);

namespace {root_name} {{
{nested_definition}
}};
"""

# a namespace const becomes internal linkage
# https://www.reddit.com/r/cpp_questions/comments/c96pjq/understanding_const_variables_being_local_to_a/
# so I remove const here
# even though, the declaration in the header is still const
# it somehow does link up in the test
template_file_variable_definition = """
FileBuffer {var_name}{{ content_, file_size_ }};
"""

def builtin_file_nested_definition(fpath: Path):
    assert isinstance(fpath, Path)

    builtin_var_name = builtin_file_suffix(fpath).name
    var_def = template_file_variable_definition.format(var_name = builtin_var_name)

    for namespace_name in fpath.parts[:-1]:
        var_def = f"namespace {namespace_name} {{{var_def}}};"

    return var_def
    
def builtin_file_definition(fpath: Path, root_name: str):
    assert isinstance(fpath, Path)

    content = ""
    with open(fpath, 'rb') as f_in:
        while True:
            bytes_read = f_in.read(16)
            if not bytes_read:
                break
            hex_line = ', '.join(f'0x{b:02x}' for b in bytes_read)
            content += hex_line + ',\n'

    full_name_def = builtin_file_nested_definition(fpath)
    full_def = template_definition_file.format(
            content = content,
            nested_definition = full_name_def,
            root_name = root_name)

    return full_def

template_declaration_file = """#pragma once
#include "{root_name}/type_aliases.hpp"

namespace {root_name} {{
{declarations}
}};
"""

# TODO instead of reshuffling the list from glob,
# I had to implement my own glob that can return a nested dict
def nested_sources_to_builtin_fs(source_root_dir: Path, sources_dict: dict, builtin_fs_dir: Path, root_name: str, overwrite_cmake = False, overwrite_defs = False, nesting_dirs: list = []):
    """nested_sources_to_builtin_fs(source_root_dir: Path, sources_dict: dict, builtin_fs_dir: Path, root_name: str, overwrite_cmake = False, overwrite_defs = False, nesting_dirs: list = []):

    Sets up the builtin_fs_dir directory according to the sources_dict.
    It creates the files directly under builtin_fs_dir, recursively creates
    the files in the subdirectories, creates a file with all the declarations,
    for the direct child files and for all the subdirectories. And it writes
    the template CMakeLists.txt, if needed.

    Returns (all_declarations: list, changed_def_files: bool)

    changed_def_files is True when a new definition file was written (and a
    corresponding declaration was passed) or an existing file was removed.
    In those cases, the CMakeLists.txt date is updated, so CMake reconfigures
    its targets, picks up a new file or removes an existing target.
    """

    if not builtin_fs_dir.exists():
        builtin_fs_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"done mkdir {builtin_fs_dir}")

    else:
        assert builtin_fs_dir.is_dir()

    # declarations of the files directly under this directory
    declarations = builtin_file_declaration(sources_dict["."], nesting_dirs)
    changed_def_files = False

    # definitions of the files directly under this directory
    used_files = set()
    for source_path in sources_dict["."]:
        def_file_name = builtin_file_suffix(source_path, ".cpp").name
        def_file_path = builtin_fs_dir / def_file_name

        # skip if the file is up to date with source
        uptodate = def_file_path.exists() and getmtime(def_file_path) > getmtime(source_path)
        if uptodate and not overwrite_defs:
            used_files.add(def_file_path)
            continue

        logging.debug(f"writing def file {builtin_fs_dir} -> {def_file_name}")
        def_file_content = builtin_file_definition(source_path, root_name)

        if not def_file_path.exists():
            changed_def_files = True

        with open(def_file_path, 'w') as def_file:
            def_file.write(def_file_content)

        used_files.add(def_file_path)
        logging.debug(f"wrote definitions file {def_file_path}")

    # remove not used files
    #all_cpp_files = [builtin_fs_dir / fname for fname in glob("*.cpp", root_dir=builtin_fs_dir)]
    all_cpp_files = {Path(fpath) for fpath in glob(f"{builtin_fs_dir}/*.cpp")}
    # TODO: clear this when the builtin_fs CMake is re-arranged
    test_file = builtin_fs_dir / "test.cpp"
    all_cpp_files.discard(test_file)

    #used_source_files = {source_root_dir / sfile for sfile in sources_dict["."]}
    not_used_files = all_cpp_files - used_files
    if not_used_files:
        logging.info(f"removing unused files in {builtin_fs_dir}: {not_used_files}")
        changed_def_files = True
        for fpath in not_used_files:
            fpath.unlink()

    # create all the subdirectory definitions and get their declarations
    for dir_name, content in sources_dict.items():
        if dir_name == '.':
            continue

        subdir_path = builtin_fs_dir / dir_name
        subdir_nesting = nesting_dirs + [dir_name]
        subdir_decls, changed_subdir_defs = nested_sources_to_builtin_fs(source_root_dir, content, subdir_path, root_name, overwrite_cmake, overwrite_defs, subdir_nesting)
        changed_def_files |= changed_subdir_defs

        declarations += subdir_decls

    # create the declarations file
    # if the definition files changed i.e. if there is a new file to declare
    if changed_def_files:
        decl_file_path = builtin_fs_dir / "fs.hpp"
        logging.info(f"updating {decl_file_path}")
        #if decl_file_path.exists():
        #    logging.warning(f"overwriting decl file {decl_file_path}")

        decl_file_content = template_declaration_file.format(
                root_name = root_name,
                declarations = "\n\n".join(declarations)
                )

        with open(decl_file_path, 'w') as decl_file:
            decl_file.write(decl_file_content)
            logging.debug(f"wrote declarations file {decl_file_path}")

    # create the CMakeLists.txt only in subdirectories
    # TODO: also get rid of it when CMake is ra-arranged
    cmake_lists_path = builtin_fs_dir / "CMakeLists.txt"
    if len(nesting_dirs) == 0:
        cmakelists_content = cmakelists_root
    else:
        cmakelists_content = cmakelists_subdir

    if not cmake_lists_path.exists() or overwrite_cmake:
        logging.info(f"writing {cmake_lists_path}")
        with open(cmake_lists_path, 'w') as cmake_lists_file:
            cmake_lists_file.write(cmakelists_content)

        # at the top level, also write the header files
        if len(nesting_dirs) == 0:
            with open(builtin_fs_dir / "type_aliases.hpp", 'w') as header_fbuf:
                header = builtin_fs_include_type_aliases.format(root_name = root_name)
                header_fbuf.write(header)

    elif changed_def_files:
        logging.info(f"updating date on {cmake_lists_path}")
        os.utime(cmake_lists_path)

    return declarations, changed_def_files

def sources_to_builtin_fs(source_paths: list, builtin_fs_dir: Path):
    """sources_to_builtin_fs(source_paths: list, builtin_fs_dir: Path)

    The matched files create 3 things in the builtin_fs directory:
    1) subdirectories with the <fname>.cpp files where <fname> is the matched file with _<extension>
    2) a header file fs.hpp that declares the nested namespaces of the builtin_fs under this subdirectory
    3) a copy of a template CMakeLists.txt in each subdirectory
    """

    assert builtin_fs_dir.is_dir()
    nested_sources = sources_to_nested_dict(source_paths)


def main():
    parser = argparse.ArgumentParser(description="Convert source files into builtin_fs .cpp")
    parser.add_argument("sources_directory", type=str, help="Path to the sources")

    parser.add_argument(
        "--config",
        type=str,
        default=".builtin_fs.toml",
        help="Name of the TOML file (default: .builtin_fs.toml)"
    )

    parser.add_argument(
        "--builtin-fs",
        type=str,
        default=None,
        help="Directory for a standalone builtin_fs"
    )

    parser.add_argument(
        "--namespace-name",
        type=str,
        default="builtin_fs",
        help="Alternative use-case: directory for a builtin_fs in the source tree"
    )

    parser.add_argument(
        "--overwrite-cmake",
        action='store_true',
        help="Overwrite the CMakeLists.txt templates"
    )

    parser.add_argument(
        "--overwrite-definitions",
        action='store_true',
        help="Overwrites def files ignoring modification time wrt source"
    )

    parser.add_argument(
        "--debug",
        action='store_true',
        help="Debug log level"
    )

    args = parser.parse_args()

    # Configure basic logging to print to stderr
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Determine where is the TOML config
    dir_path = Path(args.sources_directory)
    if dir_path.is_file() and dir_path.suffix == ".toml":
        directory = dir_path.parent
        filename = dir_path.name
    else:
        directory = dir_path
        filename = args.config

    source_dir_root = directory.parent.resolve()
    logging.debug(f"looking for files in the source dir {source_dir_root}")

    # Determine the builtin_fs directory
    if args.builtin_fs is None:
        # assume the intent is to configure in the builtin_fs source
        # via the bootstrap CMakeLists
        # so the output directory is the parent of the script / namespace name
        output_dir = Path(__file__).parent / args.namespace_name

    else:
        output_dir = Path(args.builtin_fs)

    output_dir.mkdir(parents=True, exist_ok=True)
    root_name = output_dir.name

    config = load_builtin_fs_toml(directory, filename)
    matched_files = match_config(directory, config)
    logging.debug(f"matched_files list in {directory}: {matched_files}")

    sources_dict = sources_to_nested_dict(matched_files)
    #pprint(sources_dict)

    #output_path = output_dir / "output"
    #with open(output_path, "w") as f:
    #    #print(config, file=f)
    #    #pprint(matched_files, stream=f)
    #    #pprint(sources_dict, stream=f)
    #    print(f"Output written to {output_path}")

    nested_sources_to_builtin_fs(source_dir_root, sources_dict, output_dir, root_name, args.overwrite_cmake, args.overwrite_definitions)

if __name__ == "__main__":
    main()
