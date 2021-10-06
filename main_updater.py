from investing_downloader import Investing_downloader
from betta_alpha import Bettas_alphas_creator

def main():
    Investing_downloader().parse_history()
    Bettas_alphas_creator().update_bettas_lists()


if __name__ == '__main__':
    main()