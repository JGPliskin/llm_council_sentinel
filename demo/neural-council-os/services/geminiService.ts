import { GoogleGenAI } from "@google/genai";
import { Message, Character } from "../types";

// Helper to ensure API key is present
const getApiKey = (): string => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) {
    console.error("API_KEY is missing from environment variables.");
    return "";
  }
  return apiKey;
};

export const sendMessageToGemini = async (
  history: Message[],
  newMessage: string,
  activeCharacters: Character[]
): Promise<string> => {
  const apiKey = getApiKey();
  if (!apiKey) return "Error: API Key missing.";

  const ai = new GoogleGenAI({ apiKey });

  // Construct a composite system instruction for the "Council"
  let combinedSystemInstruction = "";
  
  if (activeCharacters.length === 1) {
    combinedSystemInstruction = activeCharacters[0].systemInstruction;
  } else {
    combinedSystemInstruction = `You are a simulation of a specialized Neural Council consisting of the following personas. 
    
    When answering, you may respond as one of them, or simulate a dialogue between them if they would disagree. 
    ALWAYS prefix the speaker's name in bold (e.g., **Kant:**) if a specific persona is speaking.
    
    The personas are:
    ${activeCharacters.map(c => `\n- Name: ${c.name}\n  Role: ${c.role}\n  Instruction: ${c.systemInstruction}`).join('')}
    
    If the user asks a question, utilize the expertise of the active members to answer.`;
  }

  try {
    const chat = ai.chats.create({
        model: 'gemini-2.5-flash-latest',
        config: {
            systemInstruction: combinedSystemInstruction,
            temperature: 0.8,
        },
        history: history.map(h => ({
            role: h.role,
            parts: [{ text: h.content }]
        }))
    });

    const result = await chat.sendMessage({ message: newMessage });
    return result.text || "No response received.";

  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Error: System connection failed. " + (error instanceof Error ? error.message : "Unknown error");
  }
};