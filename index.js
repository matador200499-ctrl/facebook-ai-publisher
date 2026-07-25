require("dotenv").config();

const { publishToFacebook } = require("./publishFacebook");

async function main() {
  console.log("==============================");
  console.log("Facebook AI Publisher");
  console.log("==============================");

  const message =
    "✨📚 عرض جديد من مكتبة شعاع بالرحاب 📚✨\n\n" +
    "كل احتياجاتك المدرسية في مكان واحد!\n" +
    "📍 مكتبة شعاع بالرحاب\n" +
    "🚚 الدليفري متاح لجميع المناطق";

  try {
    const result = await publishToFacebook(message);

    console.log("================================");
    console.log("تم تنفيذ عملية النشر بنجاح ✅");
    console.log("Facebook Post ID:", result.id);
    console.log("================================");

  } catch (error) {
    console.error("================================");
    console.error("فشل النشر على Facebook ❌");

    if (error.response) {
      console.error("HTTP Status:", error.response.status);
      console.error(
        "Facebook Error:",
        JSON.stringify(error.response.data, null, 2)
      );
    } else {
      console.error("Error:", error.message);
    }

    console.error("================================");

    // مهم جدًا:
    // يجعل GitHub Actions أحمر عند فشل النشر
    process.exit(1);
  }
}

main();
