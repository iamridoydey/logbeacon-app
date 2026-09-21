import dotenv from "dotenv";
import process from "process"
dotenv.config();

export const config = {
    port: process.env.PORT || 3000,
    flaskApiUrl: process.env.FLASK_API_URL || "http://localhost:5000",
    sessionSecret: process.env.SESSION_SECRET,
};
