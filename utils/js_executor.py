"""
JavaScript执行器

提供JavaScript代码执行功能
"""

import subprocess
import tempfile
import os
import json
from typing import Any
from loguru import logger


class JavaScriptExecutor:
    """
    JavaScript执行器，使用Node.js子进程执行JavaScript代码
    """

    def __init__(self, js_file_path: str):
        self.js_file_path = js_file_path
        self._js_content = None
        self._load_js_content()

    def _load_js_content(self):
        """加载JavaScript内容"""
        try:
            with open(self.js_file_path, "r", encoding="utf-8") as f:
                self._js_content = f.read()
        except FileNotFoundError:
            logger.error(f"JavaScript文件未找到: {self.js_file_path}")
            self._js_content = ""

    def call(self, function_name: str, *args) -> Any:
        """
        调用JavaScript函数

        Args:
            function_name: 函数名
            *args: 函数参数

        Returns:
            函数执行结果
        """
        if not self._js_content:
            raise RuntimeError("JavaScript内容未加载")

        # 创建临时JavaScript文件
        js_code = f"""
{self._js_content}

// 调用函数并输出结果
const result = {function_name}({', '.join(repr(arg) for arg in args)});
console.log(JSON.stringify(result));
"""

        try:
            # 写入临时文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(js_code)
                temp_file_path = temp_file.name

            # 使用Node.js执行
            result = subprocess.run(
                ["node", temp_file_path], capture_output=True, text=True, timeout=10
            )

            # 清理临时文件
            os.unlink(temp_file_path)

            if result.returncode != 0:
                raise RuntimeError(f"JavaScript执行失败: {result.stderr}")

            # 解析结果
            output = result.stdout.strip()
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output

        except subprocess.TimeoutExpired:
            raise RuntimeError("JavaScript执行超时")
        except FileNotFoundError:
            raise RuntimeError("未找到Node.js，请安装Node.js以使用JavaScript执行功能")
        except Exception as e:
            raise RuntimeError(f"JavaScript执行错误: {str(e)}")

    def is_available(self) -> bool:
        """
        检查JavaScript执行器是否可用

        Returns:
            是否可用
        """
        try:
            # 尝试执行简单的JavaScript代码
            subprocess.run(["node", "--version"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
