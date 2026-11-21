// Offline diagnostic witness only. This is not linked into firmware.
#include "../../WillowCreek/Creek.h"

#include <charconv>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace {
constexpr std::size_t MaxSamples = 4096;
struct Sample { std::uint32_t uptime; int counts; };

int invalid() {
  std::cerr << "Offline replay stopped: invalid prepared trace.\n";
  return 1;
}

bool positiveToken(unsigned& value) {
  std::string token;
  if (!(std::cin >> std::setw(12) >> token) || token.size() > 10 ||
      token.front() < '0' || token.front() > '9')
    return false;
  const auto res = std::from_chars(token.data(), token.data() + token.size(), value);
  return res.ec == std::errc{} && res.ptr == token.data() + token.size();
}

bool reelToken(int& value) {
  std::string token;
  if (!(std::cin >> std::setw(8) >> token)) return false;
  if (token == "-1") { value = -1; return true; }
  if (token.size() > 4 || token.front() < '0' || token.front() > '9') return false;
  const auto res = std::from_chars(token.data(), token.data() + token.size(), value);
  return res.ec == std::errc{} && res.ptr == token.data() + token.size() && value <= 4095;
}

const char* phaseLabel(creek::Phase p) {
  using creek::Phase;
  switch (p) {
  case Phase::Ready: return "Ready";
  case Phase::Flight: return "Flight";
  case Phase::Waiting: return "Waiting";
  case Phase::Bite: return "Bite";
  case Phase::Fight: return "Fight";
  case Phase::Landed: return "Landed";
  case Phase::Lost: return "Lost";
  case Phase::Snag: return "Snag";
  case Phase::HaulingJunk: return "HaulingJunk";
  case Phase::JunkLanded: return "JunkLanded";
  }
  return "Unknown";
}
}

int main(int argc, char** argv) {
  const bool reverse = argc == 2 && std::string_view(argv[1]) == "--reverse";
  if (argc > 1 && !reverse) return invalid();
  std::string schema, source;
  unsigned count = 0;
  if (!(std::cin >> std::setw(20) >> schema >> std::setw(12) >> source) ||
      schema != "TW-REEL-REPLAY-1" || (source != "LIVE" && source != "SYNTHETIC") ||
      !positiveToken(count) || !count || count > MaxSamples)
    return invalid();
  std::vector<Sample> rows;
  rows.reserve(count);
  for (std::size_t i = 0; i < count; ++i) {
    unsigned ms;
    int counts;
    if (!positiveToken(ms) || ms > UINT32_MAX || !reelToken(counts))
      return invalid();
    rows.push_back({static_cast<std::uint32_t>(ms), counts});
  }
  std::cin >> std::ws;
  if (!std::cin.eof() || std::cin.bad()) return invalid();

  creek::Wheel wheel;
  creek::Game game;
  // Same deterministic cast+hook setup as firmware/tests/replay.cpp. No
  // accelerometer-to-cast mapping, no input synthesized from a real capture.
  if (source == "SYNTHETIC") {
    game.seed = 5359;
    game.tick(16, true, false, 0);
    game.tick(creek::castDurationMs, false, false, 0);
    game.tick(game.waitMs, false, false, 0);
    game.tick(60, false, true, 0);
    if (game.phase != creek::Phase::Fight) {
      std::cerr << "Offline replay cast/hook witness could not start.\n";
      return 1;
    }
  }

  bool haveTime = false;
  std::uint32_t priorTime = 0;
  std::size_t number = 0;
  for (const Sample& row : rows) {
    const bool fieldOK = row.counts >= 0;
    const bool hadBaseline = wheel.previous >= 0;
    const std::uint32_t elapsed = haveTime ? row.uptime - priorTime : 0;
    // Ordinary uint32 rollover yields a small positive interval. A backwards
    // discontinuity is treated conservatively as a reset, including when the
    // origin of the break cannot be observed from the trace.
    const bool reset = haveTime && elapsed > 0x7fffffffU;
    if (reset) wheel = creek::Wheel{};
    std::uint32_t valid = 0;
    const float turns = wheel.read(row.counts, fieldOK, row.uptime, reverse, &valid);
    const char* event = !fieldOK ? "invalid-field" : reset ? "uptime-reset"
      : !hadBaseline ? "baseline" : elapsed == 0 ? "duplicate-ms"
      : elapsed > 90 ? "stale-gap" : !valid ? "implausible-delta" : "accepted";
    // Only validated, game-range intervals on the SYNTHETIC test lane advance
    // the controlled fight. Never invent turns, missing packets or elapsed
    // gameplay between diagnostic rows; live-origin samples never drive it.
    const bool applied = source == "SYNTHETIC" && valid >= 12;
    if (applied) game.tick(valid, false, false, turns);

    std::cout << "{\"mode\":\"REPLAY\",\"source\":\"" << source
              << "\",\"sample\":" << number++ << ",\"event\":\"" << event
              << "\",\"counts\":" << std::lround(turns * 4096.0f)
              << ",\"valid_sample_ms\":" << valid << ",\"game_applied\":"
              << (applied ? "true" : "false") << ",\"phase\":";
    if (source == "SYNTHETIC")
      std::cout << "\"" << phaseLabel(game.phase) << "\",\"line_milliturns\":"
                << std::lround(game.line * 1000.0f) << ",\"catches\":" << game.catches;
    else
      std::cout << "null,\"line_milliturns\":null,\"catches\":null";
    std::cout << "}\n";

    haveTime = true;
    priorTime = row.uptime;
  }
}
