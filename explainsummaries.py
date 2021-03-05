from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os

load_dotenv()

webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK_URL").split(";"))
p2c_desc = ("**Tigers** @ Wild Wings - EV: 1.30\n**Millennials** @ Lovers - EV: 1.26 :cyclone:\n"
            "Jazz Hands @ **Tacos** - EV: 1.13 :sunny:\n\n"
            "This section shows all games this round with an expected EV > 1.0, given the current Webodds payout and "
            "our calculated MOFO odds.  The bolded team has the better odds. Sun2 and BH games are designated by "
            ":sunny: and :cyclone:, watch the loop!")
webhook.add_embed(DiscordEmbed(title="__Picks To Click__", description=p2c_desc))

linyd_desc = ("**Lift** @ Sunbeams - EV: 1.21, MOFO: 41.98%\n\n"
              "This section shows all of the losing bets with EV > 1.0, indicating that we think the odds are better "
              "than what the WebOdds think, and the increased payout may be worth the risk. Format is the same as "
              "above, but with the loser bolded, and their MOFO odds stated.")
webhook.add_embed(DiscordEmbed(title="__Look, I'm Not Your Dad__", description=linyd_desc))

mismatch_desc = ("Garages @ **Moist Talkers** - Website: Garages 51.22%, MOFO: **Moist Talkers** 51.82%\n"
                 "**Millennials** @ Lovers - Website: Lovers 59.76%, MOFO: **Millennials** 56.73%\n\n"
                 "This section shows all of the games where our odds disagree with the WebOdds on who will win the "
                 "game. Our winner is bolded.")
webhook.add_embed(DiscordEmbed(title="__Odds Mismatches__", description=mismatch_desc))

webhook.execute()
