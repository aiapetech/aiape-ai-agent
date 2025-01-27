import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities.hasher import Hasher
from streamlit_authenticator import stauth

if __name__ == '__main__':
    with open('../config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
    hashed_passwords = Hasher(passwords=['rvprSk6OdpXFAl'])
    print(hashed_passwords)
