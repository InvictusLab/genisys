---
status: done
created: '2026-03-04'
tags: []
priority: medium
created_at: '2026-03-04T08:22:27.742606386+00:00'
---

# Qwen Provider

> **Status**: planned · **Priority**: medium · **Created**: 2026-03-04

## Overview

<!-- What are we solving? Why now? -->

Add Alibaba Bailian's Qwen model as a model provider.

## Design

<!-- Technical approach, architecture decisions -->

- Read Alibaba Bailian's official documentation to learn about it.
- Inherit the model provider base class providers.base.LLMProvider and improve the functionality implemented by the base class.
- The chat method can be called normally.

## Plan

<!-- Break down implementation into steps -->

<!-- 💡 TIP: If your plan has >6 phases or this spec approaches
     400 lines, consider using sub-spec files:
     - IMPLEMENTATION.md for detailed implementation
     - See spec 012-sub-spec-files for guidance on splitting -->

- [x] Read the official documentation for Alibaba's Bailian platform to learn how to use the Qwen model. The documentation can be found at: https://bailian.console.aliyun.com/cn-beijing/?tab=doc#/doc.
- [x] Write the corresponding functions for providers.qwen.Qwen.
- [x] Write the corresponding unit tests in the file tests/providers/test_qwen.py.

## Test

<!-- How will we verify this works? -->

- [x] The chat method from model provider Qwen can be called normally.
- [x] Unit tests can pass.

## Notes

<!-- Optional: Research findings, alternatives considered, open questions -->
