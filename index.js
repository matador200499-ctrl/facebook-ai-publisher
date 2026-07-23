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
    await publishToFacebook(message);
  } catch (error) {
    console.error("حدث خطأ أثناء النشر.");
  }
}

main();