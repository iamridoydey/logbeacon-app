import { config } from "../config.js";

export async function flaskRequest(path, options = {}, cookie = null) {

    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    if (cookie) {
        headers["Cookie"] = cookie;
    }

    const response = await fetch(`${config.flaskApiUrl}${path}`, {
        ...options,
        headers,
    });

    const data = await response.json();
    const setCookie = response.headers.get("set-cookie");

    return { status: response.status, data, setCookie };
}
