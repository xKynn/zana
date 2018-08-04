from bot import Zana
import sys


def main():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = 'config.json'

    bot = Zana()
    bot.run()


if __name__ == '__main__':
    main()