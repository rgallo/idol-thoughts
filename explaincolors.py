from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os

load_dotenv()

# Discord Embed Colors
PINK = 16728779
RED = 13632027
ORANGE = 16752128
YELLOW = 16312092
GREEN = 8311585
BLUE = 4886754
PURPLE = 9442302
BLACK = 1

output = [
    ('**Red Hot:** Higher than the highest value at which non-shutouts have ever been recorded. (Historical: 100%, 8 pitchers)', PINK),
    ("**Hot:** At or below the maximum value at which a non-shutout has been recorded, but shutouts recorded at these values are at least significantly above the mean recorded value for shutouts. (Historical 75%, 4 pitchers)", RED),
    ("**Warm:** Lower than Hot, but still some amount above the mean recorded value for nonshutouts. (Historical: 23.08%, 130 pitchers)", ORANGE),
    ("**Tepid:** Lower than Warm, but still above the mean value for shutouts. (Historical: 10.63%, 442 pitchers)", YELLOW),
    ("**Temperate:** Lower than Tepid, but above the mean recorded value for non-shutouts. (Historical: 8.34%, 1,319 pitchers)", GREEN),
    ("**Cool:** At or above the minimum recorded value for shutouts, but below the mean recorded value for non-shutouts. (Historical: 3.59%, 4,573 pitchers)", BLUE),
    ("**Dead Cold:** Below the minimum recorded value for shutouts. (Historical: 0%, 452 pitchers)", PURPLE),
    ("All pitcher evaluations ever evaluated by us = 5.23% pitched shutouts", None)
]
webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
for line, color in output:
    webhook.add_embed(DiscordEmbed(description=line, color=color))
webhook.execute()
