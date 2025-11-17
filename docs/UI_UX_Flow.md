### UI/UX Flow + Wireframes

- Screens and transitions
  - Start Screen → Difficulty Select → Gameplay (Day/Night loop) → Summary → Win/Game Over → Start
  - In-Game Overlays: Pause Menu; Research Panel; Build Panel/Tooltips; Event Popup; HUD.

- What the player sees and can click (why)
  - Start Screen: Start, Quit. Minimal friction to play.
  - Difficulty: Easy/Medium/Hard/Extreme with short descriptors. Sets expectations.
  - Gameplay:
    - HUD: day/night indicator, HQ HP, wave counter, left-side resources.
    - Build UI: contextual buttons with tooltips (costs/benefits).
    - Research Button: opens tech tree (hard-coded nodes, clear prereqs).
    - Event Popup: appears briefly with overlay; communicates modifiers.
  - Summary: “Night Cleared” + quick recap. Reinforces progress.
  - Pause: Resume, Options, Quit to Menu.

- User journey (step-by-step)
  1) Choose difficulty.
  2) See Day popup; read resources; scan base; open Build Panel.
  3) Place economic building → read tooltip cost/impact → confirm.
  4) Open Research → select affordable tech → see dependency highlight.
  5) Let day play; watch workers and resources tick up.
  6) Event triggers; adapt (repair/build/adjust).
  7) Night hits; wave info updates; observe turrets and walls under pressure.
  8) Survive; summary pops; plan next day.

- Wireframe-style descriptions
  - HUD (top-right): Day/Night sprite + number; below it wave “spawned/total.”
  - HQ HP (top-center): graphical bar; no text clutter.
  - Resources (left-center): vertical stack, ample spacing, low-opacity background for readability.
  - Event Popup (top-middle): framed card, title color-coded (green/yellow/red), description, bullet effects; fade in/out; 3–4s.
  - Research Panel:
    - Three category boxes (Resources, Turret, NPC) with nodes (200×75).
    - Name top-left 10px; Cost top-right 10px; Unlock button bottom-center.
    - Straight connectors from parent mid-bottom to child mid-top; greyed locks on gated children.
  - Build Panel + Tooltips:
    - Click building icon → right/left tooltip shows footprint, costs, and passive output.
    - “Cannot build” states clearly indicate missing resources or blocked tiles.

- Reasons behind design
  - Fewer clicks, more clarity: essentials visible without opening menus.
  - Strong visual hierarchy: event popups and wave info don’t fight HUD for attention.
  - Teach by affordance: disabled nodes and greyed children communicate requirements.
  - Consistent placement: player forms a mental map for glanceable info.


