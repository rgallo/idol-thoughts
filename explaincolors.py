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
    ('**Red Hot:** Greater than the max non-shutout value (Only shutouts ever recorded at this value)', PINK),
    ("**Hot:** Less than or equal to the max non-shutout value and greater than or equal to (average + 3σ [three standard deviations]) shutout value (most likely shutout that isn't a guarantee)", RED),
    ("**Warm:** Less than (average + 3σ) shutout value and greater than or equal to (average + 3σ) non-shutout value", ORANGE),
    ("**Tepid:** Less than (average + 3σ) non-shutout value and greater than or equal to average shutout value", YELLOW),
    ("**Temperate:** Less than average shutout value and greater than or equal to average non-shutout value", GREEN),
    ("**Cool:** Less than average non-shutout value and greater than or equal to min shutout value (still possible, but unlikely)", BLUE),
    ("**Dead Cold:** Less than min shutout value (No shutouts ever recorded at this value)", PURPLE)
]
webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
for line, color in output:
    webhook.add_embed(DiscordEmbed(description=line, color=color))
webhook.execute()