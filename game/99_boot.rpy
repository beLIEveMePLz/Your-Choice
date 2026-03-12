# ============================================================
# Boot / startup glue
# App assembly, keymap disabling, entry label
# Version: v13 beta
# Changelog:
# - startup moved out of renderer into dedicated boot file
# - versioning kept in comments/file history, not in class names
# - robust symbol lookup via store (avoids NameError if scope is odd)
# ============================================================

#define config.window = "auto"
define config.developer = True

init -30 python:
        import renpy as rp

        def disable_keys(actions):
                for a in actions:
                        try:
                                rp.config.keymap[a] = []
                        except Exception:
                                pass

        disable_keys([
                "save", "load", "quick_save", "quick_load",
                "preferences", "help", "history", "hide_windows",
                "toggle_fullscreen", "self_voicing", "screenshot",
                "quit", "skip", "fast_skip", "toggle_afm",
                "developer", "console", "reload_game", "refresh_screens",
                "image_load_log", "director",
                "dismiss", "dismiss_hard",
        ])

init 100 python:
        import renpy as rp

        def make_app():
                st = rp.store
                GameCls = getattr(st, "Game", None)
                make_renderer_fn = getattr(st, "make_renderer", None)

                if GameCls is None:
                        raise Exception("Boot error: class Game not found. Check 00_core.rpy is present and has no compile errors.")
                if make_renderer_fn is None:
                        raise Exception("Boot error: make_renderer() not found. Check 10_renderer.rpy is present and has no compile errors.")

                app = GameCls()
                app.bind_renderer(make_renderer_fn(app.world))
                return app

label start:
    $ app = make_app()
    call screen debug_screen(app)
    return
