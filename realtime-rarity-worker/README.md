# Secure GitHub Pages rarity control

This is a one-time deployment. Afterwards, Python updates the hosted value over HTTPS without commits and open website tabs receive it within two seconds without reloading.

1. In this directory run:

   ```bash
   npx wrangler login
   npx wrangler secret put RARITY_WRITE_TOKEN
   npx wrangler deploy
   ```

   Use a long random token and keep it private. Deploy prints your Worker URL.
2. Put `https://your-worker.workers.dev/rarity` in `REMOTE_RARITY_URL` in `index.html`, then deploy that one site-code update.
3. In the terminal used to run Python:

   ```bash
   export RARITY_API_URL="https://your-worker.workers.dev/rarity"
   export RARITY_API_TOKEN="your-private-token"
   ```

The token is never put in the website or Git. Your PC makes only an outbound HTTPS request; no port is opened on it.
