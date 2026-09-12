# <img src="https://raw.githubusercontent.com/javand/ha-jw-library/main/icon.png" width="48" height="48" align="center" alt="JW Library Icon"> JW Library for Home Assistant

<p align="center">
  <img src="https://raw.githubusercontent.com/javand/ha-jw-library/main/logo.png" alt="JW Library Logo" width="160" />
</p>

<p align="center">
  <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS"></a>
  <a href="https://github.com/javand/ha-jw-library/releases"><img src="https://img.shields.io/github/v/release/javand/ha-jw-library?include_prereleases" alt="Release"></a>
  <a href="https://github.com/javand/ha-jw-library/blob/main/LICENSE"><img src="https://img.shields.io/github/license/javand/ha-jw-library" alt="License"></a>
</p>

The **JW Library** integration for Home Assistant pulls the weekly **Watchtower Study** article and **Bible Reading** directly from [wol.jw.org](https://wol.jw.org) and official JW CDN endpoints.

It is designed to pair seamlessly with your smart home routines—enabling you to stream official study audio to Google Cast / Nest Audio or other media players, read full texts in Lovelace dashboard cards, or use Home Assistant's text-to-speech (TTS) engines with automatically cleaned scripture references.

---

## Features

- **Weekly Watchtower Study**:
  - Full article text with study questions included.
  - Automatic scripture reference cleanup (`(Josh. 10:1)`, `, 2 Ki. 5:14,`) for natural, fluent text-to-speech recitation.
  - Direct MP3 audio stream URLs from official JW CDN for immediate playback on smart speakers.
  - Study article theme scripture, song numbers & titles, issue date, and study date range.
- **Weekly Bible Reading**:
  - Extracted from the Life and Ministry Meeting Workbook schedule.
  - Combined full chapter text of the assigned reading.
  - Official MP3 audio stream URL (`audio_url`) for the primary chapter.
  - Array of chapter stream dictionaries (`audio_urls`) for multi-chapter readings (e.g. Jeremiah 32 and Jeremiah 33).
- **Two-Week Window**:
  - Both **Current Week** and **Next Week** sensors are provided for preparation and routine flexibility.
- **Multi-Language Support**:
  - English, Spanish (*Español*), French (*Français*), German (*Deutsch*), Portuguese (*Português*), Italian (*Italiano*), Russian (*Русский*), and more.
- **Smart Scheduling & Efficiency**:
  - Synchronous midnight rollover schedule so your sensors update promptly at the start of each new week.
  - 12-hour background polling interval with exponential backoff retry.
  - In-memory caching of Bible audio metadata to minimize network overhead.

---

## Sensors Created

All sensors reside under a unified device (**JW Library**) in Home Assistant:

| Entity ID | Friendly Name | State | Key Attributes |
| :--- | :--- | :--- | :--- |
| `sensor.jw_library_watchtower_this_week` | Watchtower This Week | Article Title | `title`, `date_range`, `theme_scripture`, `songs`, `audio_url`, `text`, `issue`, `doc_id` |
| `sensor.jw_library_watchtower_next_week` | Watchtower Next Week | Article Title | `title`, `date_range`, `theme_scripture`, `songs`, `audio_url`, `text`, `issue`, `doc_id` |
| `sensor.jw_library_bible_reading_this_week` | Bible Reading This Week | Scripture Citation (e.g., `JEREMIAH 32-33`) | `citation`, `book_name`, `book_number`, `chapter_start`, `chapter_end`, `audio_url`, `audio_urls`, `text`, `doc_id` |
| `sensor.jw_library_bible_reading_next_week` | Bible Reading Next Week | Scripture Citation (e.g., `JEREMIAH 34-35`) | `citation`, `book_name`, `book_number`, `chapter_start`, `chapter_end`, `audio_url`, `audio_urls`, `text`, `doc_id` |

---

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant sidebar.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Add `https://github.com/javand/ha-jw-library` with Category: **Integration**.
4. Click **Download**, then restart Home Assistant when prompted.

### Method 2: Manual Installation

1. Download the latest release from the [Releases](https://github.com/javand/ha-jw-library/releases) page.
2. Copy the `custom_components/jw_library` directory into your Home Assistant `<config>/custom_components/` folder.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **JW Library**.
3. Select your preferred study language (default: English).
4. Click **Submit**.

To change the language later, click **Configure** on the JW Library integration card in Devices & Services.

---

## Example Automations & Scripts

### 1. Stream Weekly Watchtower Audio to Google Nest / Cast Speaker

Stream the official audio recording of the weekly Watchtower study directly to your Google Home, Nest Audio, or Sonos speaker:

```yaml
alias: "Play Watchtower Study on Living Room Speaker"
sequence:
  - service: media_player.play_media
    target:
      entity_id: media_player.living_room_speaker
    data:
      media_content_id: "{{ state_attr('sensor.jw_library_watchtower_this_week', 'audio_url') }}"
      media_content_type: "music"
```

### 2. Stream This Week's Bible Reading Audio

```yaml
alias: "Play Weekly Bible Reading"
sequence:
  - service: media_player.play_media
    target:
      entity_id: media_player.office_speaker
    data:
      media_content_id: "{{ state_attr('sensor.jw_library_bible_reading_this_week', 'audio_url') }}"
      media_content_type: "music"
```

> **Tip for Multi-Chapter Readings**: For readings spanning multiple chapters, `audio_urls` provides a list of chapter objects:
> ```jinja2
> {% for ch in state_attr('sensor.jw_library_bible_reading_this_week', 'audio_urls') %}
>   Chapter {{ ch.chapter }}: {{ ch.url }}
> {% endfor %}
> ```

### 3. Morning Routine Announcement (TTS)

Announce this week's Watchtower study title and theme scripture during your morning routine:

```yaml
alias: "Morning Study Briefing"
trigger:
  - platform: time
    at: "07:30:00"
action:
  - service: tts.speak
    target:
      entity_id: tts.google_en_com
    data:
      media_player_entity_id: media_player.kitchen_speaker
      message: >-
        Good morning! This week's Watchtower Study is titled
        {{ state_attr('sensor.jw_library_watchtower_this_week', 'title') }}.
        The theme scripture is {{ state_attr('sensor.jw_library_watchtower_this_week', 'theme_scripture') }}.
        This week's Bible reading is {{ states('sensor.jw_library_bible_reading_this_week') }}.
```

---

## Lovelace Dashboard Card Example

Display the study material directly in your dashboard using a Markdown card:

```yaml
type: markdown
title: "JW Study This Week"
content: >-
  ## {{ state_attr('sensor.jw_library_watchtower_this_week', 'title') }}
  **Date:** {{ state_attr('sensor.jw_library_watchtower_this_week', 'date_range') }}  
  **Theme:** *{{ state_attr('sensor.jw_library_watchtower_this_week', 'theme_scripture') }}*  
  **Songs:** {{ state_attr('sensor.jw_library_watchtower_this_week', 'songs') | join(', ') }}

  ---
  ### Bible Reading: {{ states('sensor.jw_library_bible_reading_this_week') }}
  [Listen to Watchtower Audio]({{ state_attr('sensor.jw_library_watchtower_this_week', 'audio_url') }}) | 
  [Listen to Bible Reading]({{ state_attr('sensor.jw_library_bible_reading_this_week', 'audio_url') }})
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
