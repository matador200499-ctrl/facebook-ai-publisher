require("dotenv").config();

const fs = require("fs");
const { publishToFacebook } = require("./publishFacebook");
const { topics } = require("./contentSeries");

const STATE_FILE = "./contentState.json";

function getCurrentIndex() {
  try {
    if (!fs.existsSync(STATE_FILE)) {
      return 0;
    }
    const data = JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
    return Number(data.currentIndex || 0);
  } catch (error) {
    return 0;
  }
}

function saveNextIndex(nextIndex) {
  const data = { currentIndex: nextIndex };
  fs.writeFileSync(STATE_FILE, JSON.stringify(data, null, 2), "utf8");
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
  
  if (currentIndex >= topics.length) {
      console.log("تم الانتهاء من جميع المواضيع، البدء من جديد...");
      saveNextIndex(0);
      process.exit(0);
  }

  const topic = topics[currentIndex];
  const nextIndex = (currentIndex + 1) % topics.length;

  console.log("الموضوع الحالي رقم:", currentIndex + 1);
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

    process.exit(1);
  }
}

main().catch((error) => {
  console.error("خطأ غير متوقع ❌");
  console.error(error.message);
  process.exit(1);
});
