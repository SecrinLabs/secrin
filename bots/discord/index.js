// index.js
import { Client, GatewayIntentBits } from "discord.js";
import axios from "axios";
import dotenv from "dotenv";

dotenv.config();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

client.once("ready", () => {
  console.log(`Logged in as ${client.user.tag}`);
});

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  // Check if bot was mentioned
  if (message.mentions.has(client.user)) {
    const query = message.content.replace(/<@!?\d+>/, "").trim();
    if (!query) {
      await message.reply("Please provide a question after mentioning me.");
      return;
    }

    await message.channel.sendTyping();

    try {
      const response = await axios.post(process.env.DISCORD_BOT_SERVER_URL, {
        question: query,
        user: message.author.username,
        channel: message.channel.id,
        guild: message.guild ? message.guild.id : null,
      });

      const answer = response.data.answer || "No context found.";
      await message.reply(answer);
    } catch (error) {
      console.error(error);
      await message.reply("Sorry, I had trouble processing that request.");
    }
  }
});

client.login(process.env.DISCORD_BOT_TOKEN);
