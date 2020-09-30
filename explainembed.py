from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os

load_dotenv()

s = ("🦀 **[Brock Forbes](https://blaseball-reference.com/players/brock-forbes), Crabs** "
     "(__Tepid__, __8.56 SO9__, 3.07 ERA), (26.58 OppBat★, 4.21 OppMaxBat), 0.30 D/O^2, __56.01%__\n"
     "~~------------~~ @ ~~------------~~\n"
     "🐅 **[Hiroto Wilcox](https://blaseball-reference.com/players/hiroto-wilcox), Tigers** "
     "(Tepid, __7.06 SO9__, 2.40 ERA), (22.80 OppBat★, 3.84 OppMaxBat), 0.14 D/O^2, 43.99%")


webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
webhook.add_embed(DiscordEmbed(description=s, color=16312092))

explanations = DiscordEmbed(title="How to Learn to Stop Worrying and Love the Bot")
explanations.add_embed_field(name='TIM', value='Temperature Indicator Matters. Hotter > Cooler when it comes to shutout chance. It scales from Red Hot > Hot > Warm > Tepid > Temperate > Cool > Dead Cold.  Check pins for more info on colors. __Underlined__ values have a better TIM, even when the words are the same.', inline=False)
explanations.add_embed_field(name='SO9', value='Strikeouts per 9 innings, how many strikeouts the pitcher has in an average game taking a normal amount of time (higher is better).  __Underlined__ values are in the top five values for today.')
explanations.add_embed_field(name='ERA', value='Earned Run Average, the average number of runs the pitcher allows per game (lower is better).', inline=False)
explanations.add_embed_field(name='OppBat★', value='The total number of batting stars the offensive team has (lower is better).', inline=False)
explanations.add_embed_field(name='OppMaxBat', value='The highest number of stars a single batter has (lower is better).', inline=False)
explanations.add_embed_field(name='D/O^2', value='A ratio of average defensive/pitching stars to average batting/baserunning stars (higher is better) `((pitchingstars+meandefstars)/((meanbatstars+meanrunstars) ** 2))`.', inline=False)
explanations.add_embed_field(name='Win Odds', value='The win odds straight from Blaseball.  __Underlined__ values are better odds.', inline=False)

webhook.add_embed(explanations)

webhook.execute()
