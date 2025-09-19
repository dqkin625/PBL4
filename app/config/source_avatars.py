SOURCE_AVATARS = {
    "coindesk": "https://www.nasdaq.com/sites/acquia.prod/files/2022/11/09/coindesksquare.jpg",
    "cryptonews": "https://scontent.fdad3-6.fna.fbcdn.net/v/t39.30808-6/249214679_1716654885201267_3959272122855269021_n.jpg?_nc_cat=110&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeGNR2ARyXI8LYDXI8eBLtNOAMmFNNLmLg8AyYU00uYuD6TwxsqJxLmmBwi0B8bLDPZtO-7DY0tfFysAOvEWY-AM&_nc_ohc=kqaIR6c5dqkQ7kNvwHRPnnt&_nc_oc=Adk-QeKQnqZTQlx3Kpj5cRZY3HoGD-M-jRkxu00uJQ3T6nNqza2y4FnabU2pVcoNn1Y&_nc_zt=23&_nc_ht=scontent.fdad3-6.fna&_nc_gid=2r52EfASPqdK5keSOmRwYA&oh=00_AfZ90u3owGxBFvpL1sNMs3ZX8CdrE2Cs_KMCbObuQpg1dw&oe=68D326BE",
    "coingape": "https://cdn-1.webcatalog.io/catalog/coingape/coingape-social-preview.png?v=1718618780560",
    "cointelegraph": "https://images.cointelegraph.com/cdn-cgi/image/format=auto,onerror=redirect,quality=90,width=1200/https://s3.cointelegraph.com/storage/uploads/view/8ad504119f606b2b8f4fece56680108f.jpg",
    "theblock": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDdyTfJe2gO4jnPxumJfbXhrxyAkuoaeOSdg&s",
    "utoday": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGSpwp9EvkyGdJS6bzqZSrYk93JAwUpk3FNA&s"
}

def get_source_avatar(source: str) -> str:
    if not source:
        return ""
    
    source_key = source.lower().strip()
    
    return SOURCE_AVATARS.get(source_key, "")


def get_all_source_avatars() -> dict:
    return SOURCE_AVATARS.copy()