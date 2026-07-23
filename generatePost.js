import { GoogleGenAI } from "@google/genai";
import { config } from "./config.js";

const ai = new GoogleGenAI({
  apiKey: config.geminiApiKey,
});

export async function generatePost() {
  const response = await ai.models.generateContent({
    model: "gemini-2.0-flash",
    contents:
      "اكتب منشورًا دعائيًا احترافيًا باللهجة المصرية لمكتبة شعاع بالرحاب عن الأدوات المدرسية، مع دعوة للزيارة، ولا يتجاوز 120 كلمة.",
  });

  return response.text;
}