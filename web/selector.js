/* Dependency-free lexical TF-IDF + maximal marginal relevance (MMR) selector. */
(function (root) {
  "use strict";

  function words(value) {
    return value.toLowerCase().match(/[a-z0-9]+/g) || [];
  }

  function tokenCost(text) {
    return Math.max(1, Math.ceil(text.length / 4));
  }

  function vector(tokens, idf) {
    const counts = new Map();
    for (const token of tokens) counts.set(token, (counts.get(token) || 0) + 1);
    const weights = new Map();
    let norm2 = 0;
    for (const [term, count] of counts) {
      const weight = count * idf.get(term);
      weights.set(term, weight);
      norm2 += weight * weight;
    }
    const norm = Math.sqrt(norm2);
    if (norm) for (const [term, value] of weights) weights.set(term, value / norm);
    return weights;
  }

  function cosine(a, b) {
    let sum = 0;
    for (const [term, weight] of a) sum += weight * (b.get(term) || 0);
    return sum;
  }

  function selectExemplars(query, exemplars, options = {}) {
    const k = options.k ?? 3;
    const diversity = options.diversity ?? 0.65;
    const budget = options.token_budget ?? null;
    const domain = options.domain ?? null;

    if (typeof query !== "string" || !query.trim() || query.length > 10000) {
      throw new Error("query must be nonempty text of at most 10000 characters");
    }
    if (!Number.isInteger(k) || k < 1 || k > 50) {
      throw new Error("k must be an integer between 1 and 50");
    }
    if (typeof diversity !== "number" || !Number.isFinite(diversity) || diversity < 0 || diversity > 1) {
      throw new Error("diversity must be a finite number between 0 and 1");
    }
    if (budget !== null && (!Number.isInteger(budget) || budget < 1 || budget > 100000)) {
      throw new Error("token_budget must be an integer between 1 and 100000");
    }
    if (domain !== null && (typeof domain !== "string" || domain.length > 100)) {
      throw new Error("domain must be a string of at most 100 characters");
    }
    if (!Array.isArray(exemplars) || exemplars.length > 1000) {
      throw new Error("exemplars must be an array of at most 1000 items");
    }

    const validated = [];
    const ids = new Set();
    exemplars.forEach((item, index) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) {
        throw new Error("exemplar " + index + " must be an object");
      }
      const entry = {};
      for (const key of ["id", "input", "output"]) {
        const value = item[key];
        if (typeof value !== "string" || !value.trim() || value.length > 10000) {
          throw new Error("exemplar " + index + " field '" + key + "' must be nonempty text of at most 10000 characters");
        }
        entry[key] = value;
      }
      const category = item.domain ?? "";
      if (typeof category !== "string" || category.length > 100) {
        throw new Error("exemplar " + index + " domain must be text of at most 100 characters");
      }
      entry.domain = category;
      if (ids.has(entry.id)) throw new Error("duplicate exemplar id: " + entry.id);
      ids.add(entry.id);
      if (domain === null || category.toLowerCase() === domain.toLowerCase()) validated.push(entry);
    });

    if (!validated.length) {
      return { selected: [], candidate_count: 0, estimated_tokens: 0, method: "tfidf-mmr" };
    }

    const docs = [words(query), ...validated.map(e => words(e.input))];
    const df = new Map();
    for (const document of docs) {
      for (const term of new Set(document)) df.set(term, (df.get(term) || 0) + 1);
    }
    const idf = new Map();
    for (const [term, count] of df) {
      idf.set(term, Math.log((docs.length + 1) / (count + 1)) + 1);
    }
    const vectors = docs.map(tokens => vector(tokens, idf));
    const q = vectors[0];
    const candidates = vectors.slice(1);
    const relevances = candidates.map(v => cosine(q, v));
    const remaining = validated.map((_, i) => i);
    const chosen = [];
    const selected = [];
    let consumed = 0;

    while (remaining.length && selected.length < k) {
      let winner = -1;
      let best = -Infinity;
      let bestRelevance = -Infinity;
      for (const i of remaining) {
        const cost = tokenCost(validated[i].input + "\n" + validated[i].output);
        if (budget !== null && consumed + cost > budget) continue;
        let redundancy = 0;
        for (const j of chosen) redundancy = Math.max(redundancy, cosine(candidates[i], candidates[j]));
        const score = diversity * relevances[i] - (1 - diversity) * redundancy;
        if (score > best || (score === best && relevances[i] > bestRelevance)) {
          winner = i;
          best = score;
          bestRelevance = relevances[i];
        }
      }
      if (winner < 0) break;
      const entry = validated[winner];
      const cost = tokenCost(entry.input + "\n" + entry.output);
      selected.push({
        ...entry,
        rank: selected.length + 1,
        relevance: Number(relevances[winner].toFixed(6)),
        mmr_score: Number(best.toFixed(6)),
        estimated_tokens: cost
      });
      consumed += cost;
      chosen.push(winner);
      remaining.splice(remaining.indexOf(winner), 1);
    }
    return { selected, candidate_count: validated.length, estimated_tokens: consumed, method: "tfidf-mmr" };
  }

  const api = { selectExemplars, tokenCost };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.ExemplarSelector = api;
})(globalThis);
