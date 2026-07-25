require("dotenv").config();

const fs = require("fs");
const { publishToFacebook } = require("./publishFacebook");
const { getNextTopic } = require("./contentSeries");

const STATE_FILE = "./contentState.js";

function getCurrentIndex() {
  try {
    if (!fs.existsSync(STATE_FILE)) {
      return 0;
    }

    const content = fs.readFileSync(STATE_FILE, "utf8");

    const match = content.match(/currentIndex\s*=\s*(\d+)/);

    if (match) {
      return Number(match[1]);
    }

    return 0;
  } catch (error) {
    return 0;
  }
}

function saveNextIndex(nextIndex) {
  const content = `module.exports = {
  currentIndex: ${nextIndex}
};
`;

  fs.writeFileSync(STATE_FILE, content, "utf8");
}

async function main() {
  console.log("=================================");
  console.log("Facebook AI Publisher");
  console.log("=================================");

  const pageId = process.env.FACEBOOK_PAGE_ID;
  const accessToken = process.env.FACEBOOK_PAGE_ACCESS_TOKEN;

  if (!pageId) {
    throw new Error("FACEBOOK_PAGE_ID غير موجود في GitHub Secrets");
  }

  if (!accessToken) {
    throw new Error(
      "FACEBOOK_PAGE_ACCESS_TOKEN غير موجود في GitHub Secrets"
    );
  }

  console.log("Page ID موجود ✅");
  console.log("Access Token موجود ✅");

  const currentIndex = getCurrentIndex();

  console.log("الموضوع الحالي رقم:", currentIndex + 1);

  const { topic, nextIndex } = getNextTopic();

  console.log("الموضوع:");
  console.log(topic.title);

  console.log("---------------------------------");
  console.log("جاري النشر على Facebook...");
  console.log("---------------------------------");

  try {
    const result = await publishToFacebook(topic.message);

    console.log("=================================");
    console.log("تم النشر بنجاح على Facebook ✅");
    console.log("Post ID:", result.id);
    console.log("=================================");

    saveNextIndex(nextIndex);

    console.log("تم الانتقال للموضوع التالي ✅");
    console.log("الموضوع القادم رقم:", nextIndex + 1);
  } catch (error) {
    console.error("=================================");
    console.error("فشل النشر على Facebook ❌");
    console.error("=================================");

    if (error.response?.data) {
      console.error(JSON.stringify(error.response.data, null, 2));
    } else {
      console.error(error.message);
    }

    // مهم جدًا:
    // لو النشر فشل، لا نغير رقم الموضوع
    // عشان يعيد المحاولة في التشغيل القادم
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("خطأ غير متوقع ❌");
  console.error(error.message);
  process.exit(1);
});
