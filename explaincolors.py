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
    ('**Red Hot:** Higher than the highest value at which non-shutouts have ever been recorded. (Historical: 100%)', PINK),
    ("**Hot:** At or below the maximum value at which a non-shutout has been recorded, but shutouts recorded at these values are at least significantly\* above the mean recorded value for shutouts. (Historical 15.4%)", RED),
    ("**Warm:** Lower than significantly above the mean recorded value for shutouts, but at or above a value of significantly above the mean recorded value for non-shutouts. (Historical: 9.78%)", ORANGE),
    ("**Tepid:** At or above the mean recorded value for shutouts, but also between the mean and significantly above of the mean recorded value for non-shutouts. (Historical: 6.89%)", YELLOW),
    ("**Temperate:** Below the mean recorded value for shutouts, but above the mean recorded value for non-shutouts. (Historical: 5.25%)", GREEN),
    ("**Cool:** At or above the minimum recorded value for shutouts, but below the mean recorded value for non-shutouts. (Historical: 2.93%)", BLUE),
    ("**Dead Cold:** Below the minimum recorded value for shutouts. (Historical: 0%)", PURPLE),
    ("\* Significant: Three standard deviations\nHistorical data spans middle of season 6 to near-end of season 8\nAll pitcher evaluations ever evaluated by us = 4.40% pitched shutouts", None)
]
webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
for line, color in output:
    webhook.add_embed(DiscordEmbed(description=line, color=color))
webhook.execute()