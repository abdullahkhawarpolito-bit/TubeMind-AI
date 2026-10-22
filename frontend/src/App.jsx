

import { useEffect, useRef, useState } from "react";

import ReactMarkdown from "react-markdown";

import remarkGfm from "remark-gfm";

import "./App.css";



const API_URL = "http://127.0.0.1:8000";

const STORAGE_KEY = "tubemind-conversations-v1";



const suggestions = [

  "Summarize this video",

  "What are the key takeaways?",

  "Explain the main concepts",

  "Give me a step-by-step explanation",

];



const icons = {

  play: "▶",

  plus: "+",

  chat: "▤",

  book: "▦",

  info: "ⓘ",

  link: "↗",

  trash: "×",

};



function createId() {

  return (

    globalThis.crypto?.randomUUID?.() ||

    `${Date.now()}-${Math.random().toString(36).slice(2)}`

  );

}



function newConversation() {

  return {

    id: createId(),

    title: "New Chat",

    videoUrl: "",

    videoId: "",

    videoTitle: "",

    ready: false,

    messages: [],

    updatedAt: Date.now(),

  };

}



function readConversations() {

  try {

    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");

    if (!Array.isArray(value)) return [];

    return value.filter(

      (item) =>

        item &&

        typeof item.id === "string" &&

        Array.isArray(item.messages)

    );

  } catch {

    return [];

  }

}



function getVideoId(value) {

  try {

    const url = new URL(value);

    const host = url.hostname.toLowerCase().replace(/^www\./, "");

    let id = "";



    if (host === "youtu.be") {

      id = url.pathname.split("/")[1] || "";

    } else if (

      host === "youtube.com" ||

      host === "m.youtube.com" ||

      host === "music.youtube.com"

    ) {

      const parts = url.pathname.split("/").filter(Boolean);

      if (parts[0] === "watch") {

        id = url.searchParams.get("v") || "";

      } else if (["shorts", "live", "embed"].includes(parts[0])) {

        id = parts[1] || "";

      }

    }



    return /^[a-zA-Z0-9_-]{11}$/.test(id) ? id : "";

  } catch {

    return "";

  }

}



function thumbnailUrl(id) {

  return id

    ? `https://i.ytimg.com/vi/${encodeURIComponent(id)}/hqdefault.jpg`

    : "";

}



function videoWatchUrl(id) {

  return `https://www.youtube.com/watch?v=${encodeURIComponent(id)}`;

}



function formatTime(seconds) {

  const total = Math.max(0, Math.floor(Number(seconds) || 0));

  const hours = Math.floor(total / 3600);

  const minutes = Math.floor((total % 3600) / 60);

  const secs = String(total % 60).padStart(2, "0");

  return hours

    ? `${hours}:${String(minutes).padStart(2, "0")}:${secs}`

    : `${minutes}:${secs}`;

}



async function apiRequest(endpoint, payload) {

  let response;

  try {

    response = await fetch(`${API_URL}${endpoint}`, {

      method: "POST",

      headers: { "Content-Type": "application/json" },

      body: JSON.stringify(payload),

    });

  } catch {

    throw new Error(

      "Cannot connect to FastAPI. Check that the backend is running on port 8000."

    );

  }



  const data = await response.json().catch(() => ({}));



  if (!response.ok) {

    if (response.status === 429) {

      throw new Error(

        "Gemini's API quota has been reached. Please wait for the quota to reset."

      );

    }

    if (response.status === 503) {

      throw new Error("The AI service is temporarily unavailable.");

    }

    if (response.status === 422) {

      throw new Error("Please check the video URL or question.");

    }

    throw new Error(

      typeof data.detail === "string"

        ? data.detail

        : `Request failed (HTTP ${response.status}).`

    );

  }

  return data;

}



async function fetchVideoTitle(url) {

  try {

    const response = await fetch(

      `https://www.youtube.com/oembed?url=${encodeURIComponent(url)}&format=json`

    );

    if (!response.ok) return "";

    const data = await response.json();

    return typeof data.title === "string" ? data.title : "";

  } catch {

    // Public metadata may be blocked by CORS or video privacy settings.

    return "";

  }

}



function Icon({ name, size = 20 }) {

  const common = {

    width: size,

    height: size,

    viewBox: "0 0 24 24",

    fill: "none",

    stroke: "currentColor",

    strokeWidth: 1.8,

    strokeLinecap: "round",

    strokeLinejoin: "round",

    "aria-hidden": true,

  };



  const paths = {

    chat: (

      <>

        <path d="M20 11.5a8.5 8.5 0 0 1-8.5 8.5 9 9 0 0 1-4-.9L3 20l.9-4.5a9 9 0 1 1 16.1-4Z" />

        <path d="M8 11h8M8 14h5" />

      </>

    ),

    plus: <path d="M12 5v14M5 12h14" />,

    send: <path d="m5 12 14-7-4 14-3-6-7-1ZM12 13l7-8" />,

    trash: (

      <>

        <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v5M14 11v5" />

      </>

    ),

    link: (

      <>

        <path d="M10 13a5 5 0 0 0 7 .2l3-3a5 5 0 0 0-7-7l-1.7 1.7" />

        <path d="M14 11a5 5 0 0 0-7-.2l-3 3a5 5 0 0 0 7 7l1.7-1.7" />

      </>

    ),

    book: (

      <>

        <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v17H6.5A2.5 2.5 0 0 1 4 17.5Z" />

        <path d="M4 17.5A2.5 2.5 0 0 1 6.5 15H20M8 7h8M8 10h6" />

      </>

    ),

    info: (

      <>

        <circle cx="12" cy="12" r="9" />

        <path d="M12 11v5M12 8h.01" />

      </>

    ),

    menu: <path d="M4 7h16M4 12h16M4 17h16" />,

    close: <path d="M5 5l14 14M19 5 5 19" />,

    external: <path d="M14 4h6v6M20 4l-9 9M20 14v6H4V4h6" />,

    check: <path d="m5 12 4 4L19 6" />,

    spark: (

      <>

        <path d="m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5Z" />

      </>

    ),

  };



  return <svg {...common}>{paths[name] || paths.spark}</svg>;

}



function Brand({ compact = false }) {

  return (

    <div className="tm-brand">

      <div className="tm-brand-mark">

        <span>▶</span>

      </div>

      {!compact && (

        <div>

          <div className="tm-brand-name">

            TubeMind <span>AI</span>

          </div>

          <div className="tm-brand-caption">CHAT WITH YOUTUBE VIDEOS</div>

        </div>

      )}

    </div>

  );

}



function App() {

  const [conversations, setConversations] = useState(readConversations);

  const [activeId, setActiveId] = useState(null);

  const [draftUrl, setDraftUrl] = useState("");

  const [question, setQuestion] = useState("");

  const [processing, setProcessing] = useState(false);

  const [answering, setAnswering] = useState(false);

  const [error, setError] = useState("");

  const [page, setPage] = useState("chat");

  const [sidebarOpen, setSidebarOpen] = useState(false);



  const endRef = useRef(null);

  const activeIdRef = useRef(activeId);

  const busyRef = useRef(false);



  const active =

    conversations.find((conversation) => conversation.id === activeId) ||

    null;



  useEffect(() => {

    activeIdRef.current = activeId;

  }, [activeId]);



  useEffect(() => {

    try {

      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));

    } catch {

      // Storage can be unavailable or full.

    }

  }, [conversations]);



  useEffect(() => {

    endRef.current?.scrollIntoView({

      behavior: "smooth",

      block: "nearest",

    });

  }, [active?.messages, answering]);



  function updateConversation(id, updater) {

    setConversations((previous) =>

      previous.map((item) => (item.id === id ? updater(item) : item))

    );

  }



  function selectConversation(item) {

    if (busyRef.current) return;

    setActiveId(item.id);

    setDraftUrl(item.videoUrl || "");

    setQuestion("");

    setError("");

    setPage("chat");

    setSidebarOpen(false);

  }



  function startNewChat() {

    if (busyRef.current) return;

    setActiveId(null);

    setDraftUrl("");

    setQuestion("");

    setError("");

    setPage("chat");

    setSidebarOpen(false);

  }



  function deleteConversation(id) {

    if (busyRef.current) return;

    setConversations((previous) =>

      previous.filter((item) => item.id !== id)

    );

    if (activeId === id) startNewChat();

  }



  async function processVideo(event) {

    event.preventDefault();

    const url = draftUrl.trim();

    const videoId = getVideoId(url);



    if (busyRef.current) return;

    if (!videoId) {

      setError("Please enter a valid YouTube video URL.");

      return;

    }



    busyRef.current = true;

    setProcessing(true);

    setError("");



    try {

      const data = await apiRequest("/index-video", { url });

      const confirmedId = data.video_id || videoId;

      const title =

        (await fetchVideoTitle(videoWatchUrl(confirmedId))) ||

        "YouTube video";



      const existing =

        active?.videoId === confirmedId ? active : null;



      if (existing) {

        updateConversation(existing.id, (item) => ({

          ...item,

          videoUrl: url,

          videoTitle: title,

          ready: true,

          updatedAt: Date.now(),

        }));

      } else {

        const created = {

          ...newConversation(),

          title: title === "YouTube video" ? "Video conversation" : title,

          videoUrl: url,

          videoId: confirmedId,

          videoTitle: title,

          ready: true,

        };

        setConversations((previous) => [created, ...previous]);

        setActiveId(created.id);

        activeIdRef.current = created.id;

      }

    } catch (err) {

      setError(err.message || "Unable to process this video.");

    } finally {

      busyRef.current = false;

      setProcessing(false);

    }

  }



  async function sendQuestion(event, suggestedText = "") {

    event?.preventDefault();

    const text = (suggestedText || question).trim();



    if (!text || !active?.ready || busyRef.current) return;



    const conversationId = active.id;

    const videoUrl = active.videoUrl;

    const history = active.messages

      .filter(

        (message) =>

          message.role === "assistant" ||

          (message.role === "user" && message.completed)

      )

      .slice(-10)

      .map((message) => ({

        role: message.role,

        content: message.text,

      }));



    busyRef.current = true;

    setAnswering(true);

    setError("");

    setQuestion("");



    updateConversation(conversationId, (item) => ({

      ...item,

      messages: [

        ...item.messages,

        {

          id: createId(),

          role: "user",

          text,

          completed: false,

        },

      ],

    }));



    try {

      const data = await apiRequest("/ask", {

        url: videoUrl,

        question: text,

        history,

      });



      if (typeof data.answer !== "string") {

        throw new Error("The backend returned an invalid answer.");

      }



      updateConversation(conversationId, (item) => {

        const messages = [...item.messages];

        const last = messages[messages.length - 1];



        if (last?.role === "user" && !last.completed) {

          messages[messages.length - 1] = {

            ...last,

            completed: true,

          };

        }



        messages.push({

          id: createId(),

          role: "assistant",

          text: data.answer,

          sources: Array.isArray(data.sources) ? data.sources : [],

        });



        return {

          ...item,

          title:

            item.messages.filter((message) => message.role === "user")

              .length === 0

              ? text.slice(0, 52)

              : item.title,

          messages,

          updatedAt: Date.now(),

        };

      });

    } catch (err) {

      setError(err.message || "Unable to generate an answer.");

      setQuestion(text);



      updateConversation(conversationId, (item) => ({

        ...item,

        messages: item.messages.filter(

          (message) => message.completed !== false

        ),

      }));

    } finally {

      busyRef.current = false;

      setAnswering(false);

    }

  }



  const recent = [...conversations].sort(

    (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)

  );



  return (

    <div className="tm-app">

      {sidebarOpen && (

        <button

          className="tm-backdrop"

          aria-label="Close sidebar"

          onClick={() => setSidebarOpen(false)}

        />

      )}



      <aside className={`tm-sidebar ${sidebarOpen ? "is-open" : ""}`}>

        <div className="tm-sidebar-top">

          <Brand />

          <button

            className="tm-mobile-close"

            onClick={() => setSidebarOpen(false)}

            aria-label="Close menu"

          >

            <Icon name="close" />

          </button>

        </div>



        <button

          className="tm-new-chat"

          onClick={startNewChat}

          disabled={processing || answering}

        >

          <Icon name="plus" size={19} />

          New Chat

        </button>



        <div className="tm-side-section">WORKSPACE</div>

        <nav className="tm-nav">

          {[

            ["chat", "chat", "AI Chat"],

            ["how", "book", "How it works"],

            ["about", "info", "About TubeMind"],

          ].map(([key, icon, label]) => (

            <button

              key={key}

              className={`tm-nav-item ${page === key ? "active" : ""}`}

              onClick={() => {

                setPage(key);

                setSidebarOpen(false);

              }}

            >

              <Icon name={icon} size={19} />

              {label}

            </button>

          ))}

        </nav>



        <div className="tm-side-section tm-recent-heading">

          <span>RECENT CONVERSATIONS</span>

          <span className="tm-count">{recent.length}</span>

        </div>



        <div className="tm-recent-list">

          {recent.length === 0 ? (

            <p className="tm-empty-history">

              Your video conversations will appear here.

            </p>

          ) : (

            recent.map((item) => (

              <div

                className={`tm-history-row ${

                  activeId === item.id ? "selected" : ""

                }`}

                key={item.id}

              >

                <button

                  className="tm-history-select"

                  onClick={() => selectConversation(item)}

                  disabled={processing || answering}

                  title={item.title}

                >

                  <Icon name="chat" size={17} />

                  <span>{item.title}</span>

                </button>

                <button

                  className="tm-history-delete"

                  title="Delete conversation"

                  aria-label={`Delete ${item.title}`}

                  onClick={() => deleteConversation(item.id)}

                  disabled={processing || answering}

                >

                  <Icon name="trash" size={16} />

                </button>

              </div>

            ))

          )}

        </div>



        <div className="tm-sidebar-bottom">

          <div className="tm-powered">

            <span className="tm-powered-dot" />

            Gemini-powered RAG

          </div>

          <div className="tm-stack">React · FastAPI · ChromaDB</div>

        </div>

      </aside>



      <div className="tm-main">

        <header className="tm-topbar">

          <div className="tm-topbar-left">

            <button

              className="tm-menu-button"

              aria-label="Open menu"

              onClick={() => setSidebarOpen(true)}

            >

              <Icon name="menu" />

            </button>

            <div>

              <div className="tm-page-label">WORKSPACE / AI CHAT</div>

              <h1>

                {page === "chat"

                  ? "Video intelligence"

                  : page === "how"

                  ? "How it works"

                  : "About TubeMind AI"}

              </h1>

            </div>

          </div>

          <div className="tm-topbar-right">

            <span className="tm-ai-pill">

              <Icon name="spark" size={16} />

              Powered by Gemini

            </span>

          </div>

        </header>



        {page === "chat" ? (

          <main className="tm-workspace">

            <div className="tm-workspace-heading">

              <div>

                <div className="tm-eyebrow">

                  <span className="tm-red-dot" />

                  YOUR AI VIDEO COMPANION

                </div>

                <h2>

                  Watch less. <span>Understand more.</span>

                </h2>

                <p>

                  Turn any supported YouTube transcript into a conversation.

                  Ask questions, discover insights, and jump to exact moments.

                </p>

              </div>

            </div>



            <section className="tm-video-panel">

              <div className="tm-panel-title">

                <div className="tm-panel-icon">

                  <Icon name="link" size={20} />

                </div>

                <div>

                  <h3>Connect a YouTube video</h3>

                  <p>Paste a link to unlock AI-powered answers.</p>

                </div>

              </div>



              <form className="tm-url-form" onSubmit={processVideo}>

                <div className="tm-url-input-wrap">

                  <Icon name="link" size={19} />

                  <input

                    type="url"

                    value={draftUrl}

                    onChange={(event) => {

                      setDraftUrl(event.target.value);

                      setError("");

                    }}

                    placeholder="Paste a YouTube video URL..."

                    aria-label="YouTube video URL"

                    disabled={processing || answering}

                    required

                  />

                </div>

                <button

                  type="submit"

                  className="tm-primary-button"

                  disabled={processing || answering}

                >

                  {processing ? "Processing..." : "Analyze video"}

                  {!processing && <Icon name="spark" size={17} />}

                </button>

              </form>



              {active?.ready && (

                <div className="tm-video-preview">

                  <a

                    className="tm-thumbnail"

                    href={videoWatchUrl(active.videoId)}

                    target="_blank"

                    rel="noopener noreferrer"

                    title="Watch on YouTube"

                  >

                    <img

                      src={thumbnailUrl(active.videoId)}

                      alt="Connected YouTube video thumbnail"

                    />

                    <span className="tm-thumbnail-play">▶</span>

                  </a>

                  <div className="tm-video-details">

                    <div className="tm-video-status">

                      <Icon name="check" size={15} />

                      TRANSCRIPT READY

                    </div>

                    <h4>{active.videoTitle || "YouTube video"}</h4>

                    <p>Ask TubeMind anything about this video.</p>

                    <a

                      href={videoWatchUrl(active.videoId)}

                      target="_blank"

                      rel="noopener noreferrer"

                      className="tm-video-link"

                    >

                      Open on YouTube

                      <Icon name="external" size={15} />

                    </a>

                  </div>

                </div>

              )}

            </section>



            <section className="tm-chat-panel">

              <div className="tm-chat-header">

                <div className="tm-chat-header-title">

                  <div className="tm-assistant-avatar">✦</div>

                  <div>

                    <h3>TubeMind Assistant</h3>

                    <p>

                      {active?.ready

                        ? "Ready to explore your video"

                        : "Connect a video to begin"}

                    </p>

                  </div>

                </div>

                <div className="tm-chat-header-status">

                  <span className="tm-online-dot" />

                  {active?.ready ? "Video connected" : "Waiting for video"}

                </div>

              </div>



              <div className="tm-chat-scroll">

                {!active?.messages?.length ? (

                  <div className="tm-welcome">

                    <div className="tm-welcome-icon">

                      <Icon name="spark" size={34} />

                    </div>

                    <div className="tm-welcome-kicker">

                      MEET YOUR VIDEO ASSISTANT

                    </div>

                    <h3>Every video has more to discover.</h3>

                    <p>

                      {active?.ready

                        ? "Your transcript is ready. Start with a question or choose a suggestion."

                        : "Connect a YouTube video above, then ask anything about its content."}

                    </p>

                    <div className="tm-suggestions">

                      {suggestions.map((item) => (

                        <button

                          key={item}

                          disabled={!active?.ready || processing || answering}

                          onClick={() => sendQuestion(null, item)}

                        >

                          <Icon name="spark" size={16} />

                          {item}

                          <span>↗</span>

                        </button>

                      ))}

                    </div>

                  </div>

                ) : (

                  <div className="tm-messages">

                    {active.messages.map((message) => (

                      <div

                        className={`tm-message tm-${message.role}`}

                        key={message.id}

                      >

                        {message.role === "assistant" && (

                          <div className="tm-message-avatar">✦</div>

                        )}

                        <div className="tm-message-content">

                          <div className="tm-message-name">

                            {message.role === "user" ? "You" : "TubeMind AI"}

                          </div>

                          {message.role === "assistant" ? (

                            <div className="tm-markdown">

                              <ReactMarkdown

                                remarkPlugins={[remarkGfm]}

                                components={{

                                  a: ({ node, ...props }) => (

                                    <a

                                      {...props}

                                      target="_blank"

                                      rel="noopener noreferrer"

                                    />

                                  ),

                                }}

                              >

                                {message.text}

                              </ReactMarkdown>

                            </div>

                          ) : (

                            <p>{message.text}</p>

                          )}



                          {message.role === "assistant" &&

                            message.sources?.length > 0 && (

                              <div className="tm-sources">

                                <div className="tm-sources-label">

                                  VIDEO REFERENCES

                                </div>

                                <div className="tm-source-links">

                                  {message.sources.map((source, index) => (

                                    <a

                                      key={`${source.start}-${index}`}

                                      href={source.url}

                                      target="_blank"

                                      rel="noopener noreferrer"

                                    >

                                      <span>▶</span>

                                      {formatTime(source.start)}

                                    </a>

                                  ))}

                                </div>

                              </div>

                            )}

                        </div>

                      </div>

                    ))}



                    {answering && (

                      <div className="tm-thinking">

                        <div className="tm-message-avatar">✦</div>

                        <div>

                          <div className="tm-message-name">TubeMind AI</div>

                          <div className="tm-thinking-bubble">

                            <span />

                            <span />

                            <span />

                            <small>Analyzing transcript...</small>

                          </div>

                        </div>

                      </div>

                    )}

                    <div ref={endRef} />

                  </div>

                )}

              </div>



              <div className="tm-chat-bottom">

                {error && (

                  <div className="tm-error" role="alert">

                    {error}

                  </div>

                )}

                <form className="tm-composer" onSubmit={sendQuestion}>

                  <Icon name="spark" size={21} />

                  <input

                    type="text"

                    value={question}

                    onChange={(event) => setQuestion(event.target.value)}

                    placeholder={

                      active?.ready

                        ? "Ask anything about this video..."

                        : "Connect a video to start chatting..."

                    }

                    aria-label="Ask a question"

                    disabled={!active?.ready || processing || answering}

                  />

                  <button

                    type="submit"

                    aria-label="Send question"

                    disabled={

                      !active?.ready ||

                      processing ||

                      answering ||

                      !question.trim()

                    }

                  >

                    <Icon name="send" size={20} />

                  </button>

                </form>

                <p className="tm-disclaimer">

                  TubeMind answers from available transcripts. Verify important

                  details using the original video.

                </p>

              </div>

            </section>

          </main>

        ) : (

          <main className="tm-info-page">

            {page === "how" ? (

              <>

                <div className="tm-eyebrow">BEHIND THE TECHNOLOGY</div>

                <h2>From video to knowledge.</h2>

                <p>

                  TubeMind AI uses Retrieval-Augmented Generation (RAG) to

                  answer questions grounded in YouTube transcripts.

                </p>

                <div className="tm-info-grid">

                  {[

                    ["01", "Connect", "Paste a YouTube video link."],

                    ["02", "Extract", "Retrieve the available transcript."],

                    ["03", "Index", "Chunk and embed text into ChromaDB."],

                    ["04", "Retrieve", "Find transcript passages related to your question."],

                    ["05", "Generate", "Use Gemini to answer with video references."],

                  ].map(([number, title, description]) => (

                    <div className="tm-info-step" key={number}>

                      <span>{number}</span>

                      <h3>{title}</h3>

                      <p>{description}</p>

                    </div>

                  ))}

                </div>

              </>

            ) : (

              <>

                <div className="tm-eyebrow">ABOUT THE PROJECT</div>

                <h2>Meet TubeMind AI.</h2>

                <p>

                  TubeMind AI is a full-stack Retrieval-Augmented Generation

                  application that lets users explore YouTube videos through

                  natural-language questions.

                </p>

                <div className="tm-about-card">

                  <h3>Built for deeper understanding</h3>

                  <p>

                    It combines transcript extraction, semantic search,

                    contextual follow-up questions, Gemini AI, and clickable

                    video timestamps in one interactive experience.

                  </p>

                  <div className="tm-tech-tags">

                    {[

                      "React",

                      "FastAPI",

                      "Python",

                      "Gemini",

                      "ChromaDB",

                      "RAG",

                    ].map((tech) => (

                      <span key={tech}>{tech}</span>

                    ))}

                  </div>

                </div>

              </>

            )}

          </main>

        )}

      </div>

    </div>

  );

}



export default App;
