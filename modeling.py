ALERTS = [
  {
    "alert_id": "a1",
    "title": "Boil Water Advisory",
    "text": "Boil water before drinking or cooking until further notice. Use bottled water if available. Check official updates for status.",
    "required_actions": ["boil water", "use bottled water", "check updates"]
  },
  {
    "alert_id": "a2",
    "title": "Severe Storm Warning",
    "text": "Severe storm approaching. Stay indoors, away from windows. Avoid travel unless necessary. Monitor official alerts.",
    "required_actions": ["stay indoors", "avoid windows", "avoid travel", "monitor alerts"]
  },
  {
    "alert_id": "a3",
    "title": "High Wind Warning",
    "text": "Northeast winds 30 to 45 mph with gusts up to 60 mph expected. High winds may move loose debris, damage property, and cause power outages. Travel could be difficult. People are urged to secure loose objects that could be blown around or damaged by the wind.",
    "required_actions": ["secure loose objects", "prepare for power outages", "use caution while traveling"]

  },
  {
  "alert_id": "a4",
  "title": "Ashfall Advisory",
  "text": "Volcanic ashfall possible across affected areas. Persons with respiratory illnesses should remain indoors to avoid inhaling ash particles. All persons outside should cover their mouth and nose with a mask or cloth. Reduced visibility and minor damage are possible.",
  "required_actions": ["stay indoors if respiratory illness", "cover mouth and nose", "limit outdoor exposure"]
  },
  {
  "alert_id": "a5",
  "title": "Flood Advisory",
  "text": "Recent heavy rain caused flooding in the area. Although the heaviest rain has ended, additional showers are possible. Continue to heed remaining road closures and be aware of lingering flooding impacts.",
  "required_actions": ["avoid flooded roads", "heed road closures", "remain alert for additional rainfall"]
  },
  {
  "alert_id": "a6",
  "title": "Dense Fog Advisory",
  "text": "Dense fog with visibility down to a quarter mile is expected. Low visibility could make driving hazardous. If driving, slow down, use headlights, and leave plenty of distance between vehicles.",
  "required_actions": ["slow down while driving", "use headlights", "increase following distance"]
  },
  {
  "alert_id": "a7",
  "title": "Cold Weather Advisory",
  "text": "Very cold wind chill temperatures are expected, with frostbite possible on exposed skin in as little as 30 minutes. Use caution while outdoors and dress appropriately for the cold. Ensure outdoor animals have adequate shelter, food, and unfrozen water.",
  "required_actions": ["wear warm clothing", "limit time outdoors", "use caution while outside", "provide shelter for animals"]
  },
  {
  "alert_id": "a8",
  "title": "Severe Thunderstorm Warning",
  "text": "A severe thunderstorm with damaging wind gusts is moving through the area. Tornadoes can develop quickly from severe thunderstorms. Move to an interior room on the lowest floor of a sturdy building and be prepared to act quickly if a tornado is spotted.",
  "required_actions": ["move to interior room", "stay on lowest floor", "seek shelter in sturdy building", "monitor storm conditions"]
 },
 {
  "alert_id": "a9",
  "title": "Ice Storm Warning",
  "text": "Significant icing is expected, making roads, bridges, and sidewalks very slippery. Travel is strongly discouraged. If travel is unavoidable, use extreme caution and carry emergency supplies. Prepare for possible power outages.",
  "required_actions": ["avoid travel", "use extreme caution if traveling", "carry emergency supplies", "prepare for power outages"]
 },
 {
  "alert_id": "a10",
  "title": "Freeze Watch",
  "text": "Sub-freezing temperatures are possible, which could damage crops, sensitive vegetation, and outdoor plumbing. Strong winds may also make driving difficult. Take steps now to protect plants, secure outdoor objects, and prepare plumbing for freezing conditions.",
  "required_actions": ["protect tender plants", "secure outdoor objects", "prepare outdoor plumbing", "use caution while driving"]
 },
 {
  "alert_id": "a11",
  "title": "Rip Current Statement",
  "text": "Dangerous rip currents and large breaking waves are expected. Inexperienced swimmers should remain out of the water. Swim near a lifeguard, and if caught in a rip current, relax and float rather than swimming against it.",
  "required_actions": ["stay out of the water if inexperienced", "swim near a lifeguard", "float if caught in a rip current", "do not swim against the current"]
},
{
  "alert_id": "a12",
  "title": "High Surf Advisory",
  "text": "Large breaking waves and dangerous surf conditions are expected along the coast. Swimming and surfing may be hazardous, and rip currents can sweep swimmers into deeper water.",
  "required_actions": ["avoid swimming in rough surf", "stay near lifeguards", "use caution near the shoreline"]
},
{
  "alert_id": "a13",
  "title": "Brisk Wind Advisory",
  "text": "Brisk winds are expected over coastal waters, with increasing wind speeds and reduced visibility at times due to blowing snow. Conditions may be hazardous for marine activities.",
  "required_actions": ["use caution on the water", "secure vessels and equipment", "avoid hazardous marine conditions"]
},
{
  "alert_id": "a14",
  "title": "High Wind Warning",
  "text": "Strong northeast winds with gusts up to 60 mph are expected. High winds may move loose debris, damage property, and cause power outages. Travel could be difficult, especially in exposed areas.",
  "required_actions": ["secure loose objects", "prepare for power outages", "use caution while traveling"]
},
{
  "alert_id": "a15",
  "title": "Small Craft Advisory",
  "text": "Hazardous marine conditions are expected with strong winds and elevated seas. Conditions will be dangerous for small vessels, especially for inexperienced mariners.",
  "required_actions": ["avoid hazardous marine conditions", "delay travel for small vessels", "use caution on the water"]
},
{
  "alert_id": "a16",
  "title": "Gale Warning",
  "text": "Strong gale-force winds are expected over coastal waters, producing very hazardous marine conditions. High winds and reduced visibility may make navigation dangerous, especially for smaller vessels.",
  "required_actions": ["avoid hazardous marine conditions", "delay marine travel", "secure vessels and equipment"]
},
{
  "alert_id": "a17",
  "title": "Heavy Freezing Spray Advisory",
  "text": "Moderate freezing spray and strong winds are creating hazardous marine conditions. Ice accumulation on vessels may affect stability, damage equipment, and reduce visibility, making navigation dangerous.",
  "required_actions": ["remain in port or seek safe harbor", "prepare for ice accumulation on vessels", "secure lifesaving and vessel equipment"]
}]

def variants_from_alert(alert_text):
    # A: original
    A = alert_text.strip()

    # B: action-first bullets (rule-based)
    # (Very simple; you can improve this once your pipeline works.)
    B = (
        "DO THIS NOW:\n"
        "- Follow the safety actions listed below.\n"
        "- If you are unsure, monitor official updates.\n\n"
        "ALERT DETAILS:\n" + A
    )

    # C: plain language rewrite (light rule-based placeholder)
    C = (
        "Important safety message:\n"
        + re.sub(r"\bmonitor\b", "check", A, flags=re.IGNORECASE)
        .replace("unless necessary", "if you can avoid it")
    )

    # D: constraint-aware addendum (generic)
    D = (
        A
        + "\n\nIf you cannot do the main action (e.g., cannot travel or do not have supplies), "
          "stay as safe as possible where you are and keep checking official updates."
    )

    return {"A_control": A, "B_action_first": B, "C_plain": C, "D_constraint": D}


