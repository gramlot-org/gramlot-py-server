"""Flask hosting for the experimental Gramlot runtime."""

__all__ = ["NativeHtmlPages", "mount_native_html"]


def __getattr__(name):
    if name in {"NativeHtmlPages", "mount_native_html"}:
        from .native_html import NativeHtmlPages, mount_native_html

        return {"NativeHtmlPages": NativeHtmlPages, "mount_native_html": mount_native_html}[name]
    if name == "mount_gramlot":
        from .application import mount_gramlot

        return mount_gramlot
    raise AttributeError(name)
