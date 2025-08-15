# Kick to Multishock Bridge

This application acts as a bridge between Kick's webhook events and the Multishock application. It allows you to trigger actions in Multishock based on events from your Kick channel, such as follows, subscriptions, and gifted subscriptions.

## Features

-   Receives webhook events from Kick for:
    -   Follows
    -   New Subscriptions
    -   Gifted Subscriptions
    -   Resubscriptions
-   Connects to the Multishock WebSocket server.
-   Formats and sends event data to Multishock to trigger actions.
-   Securely verifies incoming webhooks using Kick's public key.

## Limitations

This bridge has the following limitations due to the current capabilities of the Kick API:

-   **Channel Point Redemptions:** The Kick API does not currently provide an event for channel point redemptions (or a similar feature like "Kicks"). Therefore, this bridge **cannot** react to these events.
-   **Subscription Tiers:** The Kick API does not provide subscription tier information in its webhook payloads. This bridge will use a default value for the subscription tier, which can be configured in the `kick_bot.py` script.

## Getting Started

Follow these steps to set up and run the Kick to Multishock bridge.

### 1. Create a Kick Developer Application

1.  Go to your Kick Account Settings and select the [Developer](https://kick.com/settings/developer) tab.
2.  Click "Create App" and fill in the required information.
3.  For the "Redirect URI", you can use `http://localhost:5000/callback` for the authentication script.
4.  Once your app is created, you will get a **Client ID** and a **Client Secret**. Keep these safe.

### 2. Get Your Authentication Tokens

To allow the bridge to access your Kick channel data, you need to get an access token and a refresh token using the provided `kick_auth.py` script.

1.  Run the authentication script:
    ```bash
    python kick_auth.py
    ```
2.  The script will prompt you for your Client ID, Client Secret, and Redirect URI. Enter the values from the Kick developer app you created in the previous step.
3.  The script will generate a URL. Open this URL in your browser, log in to your Kick account, and authorize the application. It should ask for permissions to "Read channel info", "Write to chat", and "Subscribe to events".
4.  After authorizing, you will be redirected to your Redirect URI. The URL in your browser's address bar will contain a `code` parameter (e.g., `http://localhost:5000/callback?code=...&state=...`).
5.  Copy the value of the `code` parameter and paste it into the terminal where the `kick_auth.py` script is running.
6.  The script will then fetch and print your **Access Token** and **Refresh Token**. Copy these tokens.

### 3. Configure the Bridge

Open the `kick_bot.py` file and fill in the following configuration variables at the top of the file:

-   `MULTISHOCK_AUTH_KEY`: Your Multishock authentication key. You can find this in your Multishock application's settings.
-   `KICK_API_TOKEN`: The **Access Token** you obtained in the previous step.
-   `KICK_BROADCASTER_ID`: The ID of the Kick channel you want to monitor. You can find this by going to your channel on Kick and looking at the URL (e.g., `https://kick.com/your_channel_name`). Then, use a tool like Postman or `curl` to make a GET request to `https://api.kick.com/api/v2/channels/{your_channel_name}` to get the user ID.
-   `DEFAULT_SUB_TIER`: The default subscription tier to use (e.g., "1000" for Tier 1).

### 4. Expose Your Webhook

The Kick API needs to be able to send events to your local machine. To do this, you need to expose your local server to the public internet. A tool like `ngrok` can be used for this.

1.  Install `ngrok` by following the instructions on their website.
2.  Run the following command to create a public tunnel to your local port 5000:
    ```bash
    ngrok http 5000
    ```
3.  `ngrok` will give you a public URL (e.g., `https://xxxx-xxxx-xxxx.ngrok.io`). Copy this URL.
4.  Go back to your Kick developer application settings and set the "Webhook URL" to your `ngrok` URL, followed by `/kick/webhook`. For example:
    `https://xxxx-xxxx-xxxx.ngrok.io/kick/webhook`

### 5. Run the Bridge

Now you are ready to run the bridge.

1.  Make sure you have installed the required dependencies:
    ```bash
    pip install flask websockets zeroconf requests cryptography
    ```
2.  Run the `kick_bot.py` script:
    ```bash
    python kick_bot.py
    ```

The bridge will now be running and listening for events from Kick. When an event is received, it will be sent to your Multishock application to trigger the corresponding action.
