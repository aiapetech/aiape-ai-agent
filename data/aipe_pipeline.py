from apify_client import ApifyClient
import requests, os, sys
import dotenv
import glob
import pymongo
sys.path.append(os.getcwd())
from core.config import settings
dotenv.load_dotenv()
from core.post_processing import ChainSetting, PostProcessor
from core.score_calculation import ScoreSetting, TokenInfo
from core.db import engine as postgres_engine
from datetime import datetime, timedelta
from core.x import post_to_twitter
CWD = os.getcwd()
class AIPEPipeline():
    def __init__(self,date):
        self.date = date
        settings = ChainSetting()
        self.post_processor = PostProcessor(settings, postgres_engine)
        self.token_info = TokenInfo(ScoreSetting(),postgres_engine)
    def get_x_post(self):
        date = self.date.strftime("%Y-%m-%d")
        apify_client = ApifyClient(os.getenv("APIFY_TOKEN"))
        body = {
        "end": date,
        "maxItems": 500,
        "sort": "Latest",
        "start": date,
        "startUrls": [
            "https://x.com/jessepollak",
            "https://x.com/notthreadguy",
            "https://x.com/cryptoboys27",
            "https://x.com/solana_dave2",
            "https://x.com/shawmakesmagic",
            "https://x.com/leap_xyz",
            "https://x.com/torqqqsol",
            "https://x.com/DetectivePango",
            "https://x.com/BenArmstrongsX",
            "https://x.com/kmoney_69",
            "https://x.com/Brookcalls_",
            "https://x.com/0xBender",
            "https://x.com/9gagceo",
            "https://x.com/DeFi_Cheetah",
            "https://x.com/Louround_",
            "https://x.com/2lambro",
            "https://x.com/stacy_muur",
            "https://x.com/aigc3YeHe",
            "https://x.com/ViktorDefi",
            "https://x.com/GordonGoner",
            "https://x.com/0xBludex",
            "https://x.com/yellowpantherx",
            "https://x.com/CryptoGarga",
            "https://x.com/farokh",
            "https://x.com/tobi_k300",
            "https://x.com/TheDeFISaint",
            "https://x.com/cryptowasta",
            "https://x.com/CryptoKaduna",
            "https://x.com/Degentraland",
            "https://x.com/pranksy",
            "https://x.com/zacxbt",
            "https://x.com/Mars_DeFi",
            "https://x.com/RookieXBT",
            "https://x.com/kookoocryptotv",
            "https://x.com/blknoiz06",
            "https://x.com/ColdBloodShill",
            "https://x.com/S4mmyEth",
            "https://x.com/0xSleuth_",
            "https://x.com/TonyResearch_",
            "https://x.com/KyleLDavies",
            "https://x.com/0xRamonos",
            "https://x.com/defi_mochi",
            "https://x.com/0xtuba",
            "https://x.com/Arthur_0x",
            "https://x.com/0xTindorr",
            "https://x.com/gametheorizing",
            "https://x.com/poopmandefi",
            "https://x.com/alpha_pls",
            "https://x.com/ByzGeneral",
            "https://x.com/frankdegods",
            "https://x.com/bull_bnb",
            "https://x.com/AviFelman",
            "https://x.com/Tetranode",
            "https://x.com/ChartFuMonkey",
            "https://x.com/inversebrah",
            "https://x.com/Darrenlautf",
            "https://x.com/JasonSoraVC",
            "https://x.com/Punk9277",
            "https://x.com/jkrdoc",
            "https://x.com/DefiIgnas",
            "https://x.com/MustStopMurad",
            "https://x.com/gainzy222",
            "https://x.com/Martin_bml",
            "https://x.com/LouisCooper_",
            "https://x.com/CryptoCred",
            "https://x.com/Tree_of_Alpha",
            "https://x.com/Tyler_Did_It",
            "https://x.com/CL207",
            "https://x.com/yb_effect",
            "https://x.com/CryptoShiro_",
            "https://x.com/danielesesta",
            "https://x.com/carlosroldanx",
            "https://x.com/ZssBecker",
            "https://x.com/kahincryptocu",
            "https://x.com/Alejandro_XBT",
            "https://x.com/hmalviya9",
            "https://x.com/futuristkwame",
            "https://x.com/graildoteth",
            "https://x.com/ethermage",
            "https://x.com/Poe_Ether",
            "https://x.com/thekryptoking_",
            "https://x.com/RealJonahBlake",
            "https://x.com/madapescall",
            "https://x.com/TriMaiMS",
            "https://x.com/bachkhoabnb",
            "https://x.com/Defi_Warhol",
            "https://x.com/0xCrypto_doctor",
            "https://x.com/0x_Lens",
            "https://x.com/Defi0xJeff",
            "https://x.com/SolJakey",
            "https://x.com/watashi_wu",
            "https://x.com/corehtrading",
            "https://x.com/UxGsol",
            "https://x.com/0xethermatt",
            "https://x.com/ayyyeandy",
            "https://x.com/suganarium",
            "https://x.com/The__Solstice",
            "https://x.com/ziddyten",
            "https://x.com/skilllevel7",
            "https://x.com/ai",
            "https://x.com/Loomdart",
            "https://x.com/KoroushAK",
            "https://x.com/EllioTrades",
            "https://x.com/TheCryptoDog",
            "https://x.com/Pentosh1",
            "https://x.com/CryptoKaleo",
            "https://x.com/JRNYcrypto",
            "https://x.com/CryptoWizardd",
            "https://x.com/CryptoDiffer",
            "https://x.com/AltcoinDailyio",
            "https://x.com/MoonOverlord",
            "https://x.com/CryptoNewton",
            "https://x.com/TraderMayne",
            "https://x.com/MuroCrypto",
            "https://x.com/TraderNJ1",
            "https://x.com/TheDeFiEdge",
            "https://x.com/benbybit",
            "https://x.com/aeyakovenko",
            "https://x.com/cz_binance",
            "https://x.com/beast_ico",
            "https://x.com/0xBreadguy",
            "https://x.com/beaniemaxi",
            "https://x.com/0xngmi",
            "https://x.com/punk9059",
            "https://x.com/waleswoosh",
            "https://x.com/fede_intern",
            "https://x.com/yuyue_chris",
            "https://x.com/lex_node",
            "https://x.com/milesdeutscher",
            "https://x.com/basedkarbon",
            "https://x.com/EasyEatsBodega",
            "https://x.com/zachxbt",
            "https://x.com/sgoldfed",
            "https://x.com/AndreCronjeTech",
            "https://x.com/cburniske",
            "https://x.com/jconorgrogan",
            "https://x.com/MikeIppolito_",
            "https://x.com/pythianism",
            "https://x.com/WazzCrypto",
            "https://x.com/RunnerXBT",
            "https://x.com/cryptopunk7213",
            "https://x.com/0xelonmoney",
            "https://x.com/haydenzadams",
            "https://x.com/Route2FI",
            "https://x.com/a1lon9",
            "https://x.com/0xCygaar",
            "https://x.com/digitalartchick",
            "https://x.com/functi0nZer0",
            "https://x.com/mdudas",
            "https://x.com/dfinzer",
            "https://x.com/howdymerry",
            "https://x.com/legendarygainz_",
            "https://x.com/a1lon9",
            "https://x.com/tkstanczak",
            "https://x.com/rasmr_eth",
            "https://x.com/hasufl",
            "https://x.com/liam_xbt",
            "https://x.com/mdudas",
            "https://x.com/imperooterxbt",
            "https://x.com/intern",
            "https://x.com/MaxResnick1",
            "https://x.com/tayvano_",
            "https://x.com/AltcoinBuzzio",
            "https://x.com/CryptoFeras",
            "https://x.com/AltcoinGordon",
            "https://x.com/Defi_Dad",
            "https://x.com/TraderKoz",
            "https://x.com/DaanCrypto",
            "https://x.com/CryptoMichNL",
            "https://x.com/AltcoinPsycho",
            "https://x.com/notsofast",
            "https://x.com/LadyofCrypto1",
            "https://x.com/CryptoFinally",
            "https://x.com/laurashin",
            "https://x.com/KevinSusanto",
            "https://x.com/martocsan_",
            "https://x.com/parcifap_defi",
            "https://x.com/TweetbyDominic",
            "https://x.com/OldMannCrypto",
            "https://x.com/CryptoJobs3",
            "https://x.com/CryptoDaku_",
            "https://x.com/Crypto_McKenna",
            "https://x.com/crypto_birb",
            "https://x.com/CryptosBatman",
            "https://x.com/tgd_duu",
            "https://x.com/youfadedwealth",
            "https://x.com/Crypto4bailout",
            "https://x.com/SherifDefi",
            "https://x.com/TheApeMother",
            "https://x.com/Crypto_Scient",
            "https://x.com/miragemunny",
            "https://x.com/CryptoCharmer",
            "https://x.com/Abigail8439",
            "https://x.com/TishaaWEB3",
            "https://x.com/kookoocryptotv",
            "https://x.com/cagyjan1",
            "https://x.com/web3dome",
            "https://x.com/MusubiNFT",
            "https://x.com/cryptosanthoshK",
            "https://x.com/KingKaranCrypto"
        ]
    }
        actor_client = apify_client.actor('apidojo/twitter-scraper-lite')
        call_result = actor_client.call(run_input=body)
        mongo_client = pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
        mydb = mongo_client["sightsea"]
        mycol = mydb["posts"]
        unique_data = []
        ids = []

    # Fetch and print Actor results from the run's dataset (if there are any)
        for item in apify_client.dataset(call_result['defaultDatasetId']).iterate_items():
            id = item['id']
            date_format = "%a %b %d %H:%M:%S %z %Y"
            item['createdAt'] = datetime.strptime(item['createdAt'], date_format)
            if id not in ids:
                unique_data.append(item)
                ids.append(id)
        mycol.insert_many(unique_data)
        print("Data inserted successfully")
        return unique_data
    def extract_most_mentioned_project_name(self):
        self.df_project_name = self.post_processor.extract_project_name_mongo(self.date)
        self.df_project_name.sort_values(by="ai_logic_count",ascending=False).reset_index(drop=True,inplace=True)
    def process_data(self):
        self.df_project_tokens, self.df_category, self.df_potential_tokens = self.token_info.generate_report_v2(self.df_project_name)
    def generate_x_post(self):
        tokens = self.df_potential_tokens
        potential_tokens = tokens.to_dict(orient="records")
        self.x_posts = []
        for token in potential_tokens[:2]:
            tokendata = self.token_info.get_token_info(token['id'])
            settings = ChainSetting()
            processor = PostProcessor(settings, postgres_engine)
            content = processor.generate_content(tokendata)
            self.x_posts.append(content)
        return self.x_posts
    def post_to_x(self):
        for post in self.x_posts:
            post_to_twitter(post)
if __name__ == "__main__":
    aipae_pipeline = AIPEPipeline(datetime.now()-timedelta(days=1))
    #aipae_pipeline.get_x_post()
    aipae_pipeline.extract_most_mentioned_project_name() 
    aipae_pipeline.process_data()
    aipae_pipeline.generate_x_post()
    aipae_pipeline.post_to_x()


