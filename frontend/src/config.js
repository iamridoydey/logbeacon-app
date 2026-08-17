import dotenv from "dotenv";
dotenv.config();

export const config = {
    port: process.env.PORT || 3000,
    flaskApiUrl: process.env.FLASK_API_URL || "http://localhost:5000",
    sessionSecret: process.env.SESSION_SECRET,
};
