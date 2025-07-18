import os
import re

import gradio as gr
import modelscope_studio.components.antd as antd
import modelscope_studio.components.base as ms

from .env import is_modelscope_studio
from .parse_markdown import parse_markdown


class Docs:

    def __init__(self, file_path: str):
        self.file_path = file_path
        # default current directory
        self.markdown_files = [
            filename for filename in os.listdir(os.path.dirname(file_path))
            if filename.endswith(".md")
        ]
        self.demo_modules = self._get_demo_modules()
        if is_modelscope_studio:
            self.markdown_files = list(
                filter(
                    lambda x: x.endswith("-zh_CN.md") or
                    (f"{'.'.join(x.split('.')[:-1])}-zh_CN.md" not in self.
                     markdown_files), self.markdown_files))
        else:
            self.markdown_files = list(
                filter(lambda x: not x.endswith("-zh_CN.md"),
                       self.markdown_files))

    def _get_filename(self, filename: str):
        if is_modelscope_studio:
            return f"{filename}-zh_CN.md"
        return f"{filename}.md"

    def _remove_formatter(self, markdown_text):
        pattern = r"^ *---[\s\S]*?---"
        replaced_text = re.sub(pattern, "", markdown_text)
        return replaced_text

    def _list_demos(self, dir_path: str, prefix=''):
        result = []
        if (not os.path.isdir(dir_path)):
            return result
        for name in os.listdir(dir_path):
            path = os.path.join(dir_path, name)

            if os.path.isfile(path):
                result.append(prefix + name)
            elif os.path.isdir(path):
                sub_prefix = prefix + name + '/'
                result.extend(self._list_demos(path, sub_prefix))

        return result

    def _get_demo_modules(self):
        import importlib.util

        demos = [
            demo for demo in self._list_demos(
                os.path.join(os.path.dirname(self.file_path), "demos"))
            if demo.endswith(".py") and not demo.startswith("__")
        ]
        demo_modules = {}
        for demo in demos:
            demo_name = demo.split(".")[0]
            spec = importlib.util.spec_from_file_location(
                "demo",
                os.path.join(os.path.dirname(self.file_path), "demos", demo))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            demo_modules[demo_name] = module
        return demo_modules

    def _read_file(self, relative_path: str):
        with open(os.path.join(os.path.dirname(self.file_path), relative_path),
                  "r") as f:
            return f.read()

    def _render_demo(self,
                     demo_name,
                     prefix='',
                     suffix='',
                     position="left",
                     collapsible=False,
                     fixed=False,
                     title=''):
        content = self._read_file(f"./demos/{demo_name}.py")
        module = self.demo_modules[demo_name]
        with antd.Card(styles=dict(body=dict(padding=10)),
                       elem_style=dict(margin="8px 0")):
            if title:
                with ms.Slot("title"):
                    ms.Text(title)
            with antd.Row(align="stretch", wrap=True, gutter=[8, 8]):
                with antd.Col(sm=dict(span=24 if position == "bottom" else 10,
                                      order=2 if position == "bottom" else 1),
                              xs=dict(span=24, order=2)):

                    def render_code():
                        with antd.Row(elem_style=dict(height='100%'),
                                      gutter=[8, 8]):
                            with antd.Col(sm=0, xs=24):
                                antd.Divider(type="horizontal",
                                             variant="dashed",
                                             elem_style=dict(width='100%',
                                                             margin='8px 0 0'))
                            resolved_prefix = prefix + "\n" if prefix else ""
                            resolved_suffix = suffix + "\n" if suffix else ""
                            with antd.Col(sm=23, xs=24):
                                ms.Markdown(f"""{resolved_prefix}```python
{content}
  ```{resolved_suffix}""",
                                            header_links=True)

                            with antd.Col(sm=1,
                                          xs=0,
                                          elem_style=dict(height="100%")):
                                with ms.Div(elem_style=dict(
                                        display="flex",
                                        justifyContent="center",
                                        width="100%",
                                        height="100%")):
                                    antd.Divider(type="vertical",
                                                 variant="dashed",
                                                 elem_style=dict(height='100%',
                                                                 margin=0))

                    if collapsible:
                        with antd.Collapse():
                            with antd.Collapse.Item(label="Show Code",
                                                    key="code"):
                                render_code()
                    else:
                        render_code()
                with antd.Col(
                        sm=dict(span=24 if position == "bottom" else 14,
                                order=1 if position == "bottom" else 2),
                        xs=dict(span=24, order=1),
                        elem_style=dict(
                            width='100%',
                            transform="translate(0, 0)" if fixed else None)):
                    module.demo.render()

    def _render_markdown(self, markdown_file):
        items = parse_markdown(self._remove_formatter(
            self._read_file(markdown_file)),
                               read_file=self._read_file)
        for item in items:
            if item["type"] == "text":
                ms.Markdown(item["value"], header_links=True)
            elif item["type"] == "demo":
                self._render_demo(item["name"],
                                  prefix=item["prefix"],
                                  suffix=item["suffix"],
                                  position=item["position"],
                                  collapsible=item["collapsible"],
                                  fixed=item["fixed"],
                                  title=item["title"])

    def get_css(self):
        css = ""
        for demo_name in self.demo_modules:
            module = self.demo_modules[demo_name]
            if hasattr(module, "css"):
                css += module.css
        return css

    def render(self, module_name: str = None):
        parsed_filename = self._get_filename(
            module_name) if module_name else None
        with gr.Blocks() as demo:
            self._render_markdown(
                parsed_filename if parsed_filename else self.markdown_files[0])
        return demo
