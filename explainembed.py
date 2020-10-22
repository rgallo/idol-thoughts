from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os

load_dotenv()

s1 = ("💋 **[Yosh Carpenter](https://blaseball-reference.com/players/yosh-carpenter), Lovers** (~~Cool~~, __5 K9__, "
      "6.14 SO9, 3.76 ERA), (3.25★ AOB, 4.78★ MOB), 0.16 D/O^2, ~~43.76%~~ WebOdds, ~~48.87%~~ MOFO")

s2 = ("📱 **[Theodore Cervantes](https://blaseball-reference.com/players/theodore-cervantes), Millennials** "
      "(__Tepid__, __7 K9__, __6.73 SO9__, 3.88 ERA), (2.41★ AOB, 4.56★ MOB), 0.25 D/O^2, 56.24% WebOdds, 51.13% MOFO")

webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
webhook.add_embed(DiscordEmbed(description=s1, color=4886754))
webhook.add_embed(DiscordEmbed(description=s2, color=16312092))

explanations = DiscordEmbed(title="How to Learn to Stop Worrying and Love the Bot")
fields = (
     ('TIM', 'Temperature Indicator Matters. Hotter > Cooler when it comes to shutout chance. It scales from Red Hot > Hot > Warm > Tepid > Temperate > Cool > Dead Cold.  Check pins for more info on colors. __Underlined__ values have a better TIM, even when the words are the same. Games are sorted by the max temp, so most likely shutouts will be on top.'),
     ('K9', 'A calculated prediction of how many strikeouts the pitcher will pitch in 9 innings, an average game taking a normal amount of time (higher is better).  __Underlined__ values are in the top five values for today.'),
     ('SO9', 'Historical strikeouts per 9 innings, how many strikeouts the pitcher on average has previously pitched in an average game taking a normal amount of time (higher is better).  __Underlined__ values are in the top five values for today.'),
     ('ERA', 'Earned Run Average, the average number of runs the pitcher has historically allowed per game (lower is better).'),
     ('AOB', 'Average Opponent Batting, the geometric mean of batting stars the offensive team has (lower is better).'),
     ('MOB', 'Max Opponent Batting, the highest number of stars a single batter has (lower is better).'),
     ('D/O^2', 'A ratio of average defensive/pitching stars to average batting/baserunning stars (higher is better) `((pitchingstars+meandefstars)/((meanbatstars+meanrunstars) ** 2))`.'),
     ('WebOdds', 'The win odds straight from Blaseball.  ~~Strikethrough~~ values are the lesser odds.'),
     ('MOFO', "Millennials Outrageously Fabulous Odds, an alternative odds formula.  With our current data set, prior to Season 11, this picks the winner 66.32% of games, vs. WebOdds' 62.99%.  ~~Strikethrough~~ values are the lesser odds."),
)

for name, description in fields:
    explanations.add_embed_field(name=name, value=description, inline=False)

webhook.add_embed(explanations)

webhook.execute()
