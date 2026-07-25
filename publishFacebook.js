const axios = require("axios");
require("dotenv").config();

async function publishToFacebook(message) {
  const pageId = process.env.FACEBOOK_PAGE_ID;
  const accessToken = process.env.FACEBOOK_PAGE_ACCESS_TOKEN;

  if (!pageId) {
    throw new Error("FACEBOOK_PAGE_ID غير موجود في GitHub Secrets");
  }

  if (!accessToken) {
    throw new Error("FACEBOOK_PAGE_ACCESS_TOKEN غير موجود في GitHub Secrets");
  }

  console.log("Page ID موجود ✅");
  console.log("Access Token موجود ✅");
  console.log("جاري إرسال المنشور إلى Facebook...");

  try {
    const response = await axios.post(
      `https://graph.facebook.com/v23.0/${pageId}/feed`,
      {
        message: message,
        access_token: accessToken,
      }
    );

    console.log("تم النشر على Facebook بنجاح ✅");
    console.log("Post ID:", response.data.id);

    return response.data;

  } catch (error) {
    console.error("Facebook API Error ❌");

    if (error.response) {
      console.error(
        JSON.stringify(error.response.data, null, 2)
      );
    } else {
      console.error(error.message);
    }

    throw error;
  }
}

module.exports = { publishToFacebook };
