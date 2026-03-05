import os
import sys
import platform
from Variable_data import VARIABLES

if sys.version_info >= (3, 0):
    import urllib.parse

class Test_Window:
    check_var = 0
    ximc_dir = 1
    @classmethod
    def ximc_check(cls, way):
        cur_dir = os.path.abspath(os.path.dirname(way))
        ximc_dir = os.path.join(cur_dir, "ximc")
        ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python")
        sys.path.append(ximc_package_dir)
        if platform.system() == "Windows":
            arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"  #
            libdir = os.path.join(ximc_dir, arch_dir)
            os.environ["Path"] = libdir + ";" + os.environ["Path"]

        try:
            import pyximc
            from pyximc import lib, create_string_buffer, EnumerateFlags
        except ImportError as err:
            print(
                "Не могу импортировать модуль pyximc. Вероятная причина что вы изменили место testpython.py или pyximc.py файлов. Посмотрите документацию разработчиков для деталей."
            )
            return
        except OSError as err:
            if platform.system() == "Windows":
                if err.winerror == 193:
                    print(
                        "Err: The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit."
                    )
                elif err.winerror == 126:
                    print(
                        "Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing."
                    )
                else:
                    print(err)
                print(
                    "Warning: If you are using the example as the basis for your module, make sure that the dependencies installed in the dependencies section of the example match your directory structure."
                )
                print(
                    "For correct work with the library you need: pyximc.py, bindy.dll, libximc.dll, xiwrapper.dll"
                )
            else:
                print(err)
                print(
                    "Не могу загрузить libximc. Пожалуйста добавьте все библиотеки на свои места. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same"
                )
            return

        sbuf = create_string_buffer(64)
        lib.ximc_version(sbuf)
        print("Library XIMC version: " + sbuf.raw.decode().rstrip("\0"))
        # print(ximc_dir)
        cls.check_var = 1
        return ximc_dir, pyximc


if __name__ == "__main__":
    # Test_Window.ximc_check(VARIABLES.XIMC_Path)
    hh, lib = Test_Window.ximc_check(VARIABLES.XIMC_Path)
    print(hh, lib)
