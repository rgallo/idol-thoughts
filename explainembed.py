from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os

load_dotenv()

s = ("🦀 **[Brock Forbes](https://blaseball-reference.com/players/brock-forbes), Crabs** "
     "(__Tepid__, __8.56 SO9__, 3.07 ERA), (2.95★ AOB, 4.21★ MOB), 0.30 D/O^2, 56.01% WebOdds, 55.87% MOFO\n"
     "~~------------~~ @ ~~------------~~\n"
     "🐅 **[Hiroto Wilcox](https://blaseball-reference.com/players/hiroto-wilcox), Tigers** "
     "(Tepid, __7.06 SO9__, 2.40 ERA), (2.53★ AOB, 3.84★ MOB), 0.14 D/O^2, ~~43.99%~~ WebOdds, ~~44.13%~~ MOFO")


webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
webhook.add_embed(DiscordEmbed(description=s, color=16312092))

explanations = DiscordEmbed(title="How to Learn to Stop Worrying and Love the Bot")
explanations.add_embed_field(name='TIM', value='Temperature Indicator Matters. Hotter > Cooler when it comes to shutout chance. It scales from Red Hot > Hot > Warm > Tepid > Temperate > Cool > Dead Cold.  Check pins for more info on colors. __Underlined__ values have a better TIM, even when the words are the same.', inline=False)
explanations.add_embed_field(name='SO9', value='Strikeouts per 9 innings, how many strikeouts the pitcher has in an average game taking a normal amount of time (higher is better).  __Underlined__ values are in the top five values for today.')
explanations.add_embed_field(name='ERA', value='Earned Run Average, the average number of runs the pitcher allows per game (lower is better).', inline=False)
explanations.add_embed_field(name='AOB', value='Average Opponent Batting, the geometric mean of batting stars the offensive team has (lower is better).', inline=False)
explanations.add_embed_field(name='MOB', value='Max Opponent Batting, the highest number of stars a single batter has (lower is better).', inline=False)
explanations.add_embed_field(name='D/O^2', value='A ratio of average defensive/pitching stars to average batting/baserunning stars (higher is better) `((pitchingstars+meandefstars)/((meanbatstars+meanrunstars) ** 2))`.', inline=False)
explanations.add_embed_field(name='WebOdds', value='The win odds straight from Blaseball.  ~~Strikethrough~~ values are the lesser odds.', inline=False)
explanations.add_embed_field(name='MOFO', value='Millennials Outrageously Fabulous Odds, an alternative odds formula.  With our current data set, this picks the winner 66.32% of games, vs. WebOdds\' 62.99%.  ~~Strikethrough~~ values are the lesser odds.', inline=False)

webhook.add_embed(explanations)

webhook.execute()
