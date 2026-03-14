# ============================================================
# Boot / startup glue
# App assembly, keymap disabling, entry label
# Version: v13 beta hotfix
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
                "image_load_log", "director", "dismiss",
                "game_menu", "rollback", "rollforward",
        ])

        try:
                rp.clear_keymap_cache()
        except Exception:
                pass

init 100 python:
        import renpy as rp

        def make_app():
                st = rp.store
                GameCls = getattr(st, "Game", None)
                make_renderer_fn = getattr(st, "make_renderer", None)

                if GameCls is None:
                        raise Exception("Boot error: class Game not found. Check core files for compile errors.")
                if make_renderer_fn is None:
                        raise Exception("Boot error: make_renderer() not found. Check 10_renderer.rpy.")

                app = GameCls()
                app.bind_renderer(make_renderer_fn(app.world))
                return app

label start:
    jump yc_gameplay

label yc_gameplay:
    window hide
    scene black

    python:
        try:
            app = make_app()
            renpy.notify("GAMEPLAY OK")
        except Exception as e:
            renpy.notify("GAMEPLAY EXC: %r" % (e,))
            raise

    call screen debug_screen(app)
    return