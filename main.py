"""Entry point for the Stereo Vision System — User Application."""

from app.gui.main_window import MainWindow


def main() -> None:
    window = MainWindow()
    window.run()


if __name__ == "__main__":
    main()
