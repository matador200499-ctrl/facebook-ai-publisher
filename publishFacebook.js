const axios = require("axios");
require("dotenv").config();

async function publishToFacebook(message) {
  const pageId = process.env.FACEBOOK_PAGE_ID;
  const accessToken = process.env.FACEBOOK_PAGE_ACCESS_TOKEN;

  if (!pageId || !accessToken) {
    throw new Error(
      "FACEBOOK_PAGE_ID أو FACEBOOK_PAGE_ACCESS_TOKEN غير موجود في ملف .env"
    );
  }

  try {
    const response = await axios.post(
      `https://graph.facebook.com/v23.0/${pageId}/feed`,
      {
        message,
        access_token: accessToken,
      }
    );

    console.log("تم النشر على Facebook بنجاح ✅");
    console.log("Post ID:", response.data.id);

    return response.data;
  } catch (error) {
    console.error(
      "فشل النشر على Facebook ❌",
      error.response?.data || error.message
    );

    throw error;
  }
}

module.exports = { publishToFacebook };