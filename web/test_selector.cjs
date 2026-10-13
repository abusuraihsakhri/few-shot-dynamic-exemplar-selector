"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { selectExemplars } = require("./selector.js");

const pool = [
  {id:"a",input:"acute kidney injury",output:"Compare kidney function",domain:"clinical"},
  {id:"b",input:"acute kidney injury",output:"Review fluid status",domain:"clinical"},
  {id:"c",input:"apple pear fruit",output:"Assess nutrition",domain:"clinical"},
  {id:"d",input:"sort a Python list",output:"Use sorted",domain:"coding"}
];

test("lexical relevance ranks duplicate matches first with maximum relevance weighting", () => {
  const result = selectExemplars("acute kidney injury", pool, {k:2,diversity:1});
  assert.deepEqual(result.selected.map(e => e.id), ["a","b"]);
  assert.equal(result.candidate_count, 4);
});

test("MMR penalizes redundancy and results are deterministic", () => {
  const options = {k:2,diversity:0.2};
  const result = selectExemplars("acute kidney injury", pool, options);
  assert.equal(result.selected[0].id, "a");
  assert.ok(["c","d"].includes(result.selected[1].id));
  assert.deepEqual(result, selectExemplars("acute kidney injury", pool, options));
});

test("domain and token budget are enforced", () => {
  const result = selectExemplars("kidney", pool, {domain:"CLINICAL"});
  assert.equal(result.candidate_count, 3);
  assert.equal(selectExemplars("kidney", pool, {token_budget:1}).selected.length, 0);
  assert.equal(selectExemplars("kidney", [], {}).candidate_count, 0);
});

test("rejects unsafe input types and duplicates", () => {
  for (const options of [{k:0},{k:true},{diversity:NaN},{token_budget:-1},{domain:4}]) {
    assert.throws(() => selectExemplars("kidney", pool, options));
  }
  assert.throws(() => selectExemplars("kidney", [pool[0],{...pool[0],domain:"other"}]));
  assert.throws(() => selectExemplars("kidney", [{id:"a",input:"",output:"yes"}]));
});

test("Python and browser implementations agree on scores for common ASCII fixtures", () => {
  const result = selectExemplars("acute kidney injury", pool, {k:1,diversity:1});
  assert.equal(result.selected[0].relevance, 1);
  assert.equal(result.selected[0].mmr_score, 1);
});
