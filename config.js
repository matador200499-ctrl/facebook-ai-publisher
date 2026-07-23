import dotenv from "dotenv";

dotenv.config();

export const config = {
  geminiApiKey: process.env.GEMINI_API_KEY,
  facebookPageId: process.env.FACEBOOK_PAGE_ID,
  facebookPageAccessToken: process.env.FACEBOOK_PAGE_ACCESS_TOKEN,
};