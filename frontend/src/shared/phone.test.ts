import { describe, expect, it } from "vitest";

import { formatPhone, incidentContactMessage, phoneEnding, whatsAppLink } from "./phone";

describe("formatPhone", () => {
  it.each([
    ["5500900000001", "(00) 90000-0001"],
    ["5561999998888", "(61) 99999-8888"],
    ["556133334444", "(61) 3333-4444"],
  ])("formats %s as %s", (phone, expected) => {
    expect(formatPhone(phone)).toBe(expected);
  });

  it.each(["61999998888", "1999998888", "55619999988889"])(
    "keeps %s as it came when it is not a Brazilian number",
    (phone) => {
      expect(formatPhone(phone)).toBe(phone);
    },
  );
});

describe("phoneEnding", () => {
  it("returns the last four digits", () => {
    expect(phoneEnding("5500900000001")).toBe("0001");
  });
});

describe("whatsAppLink", () => {
  it("encodes the message, so a # does not cut it", () => {
    expect(whatsAppLink("5500900000001", "Incidente #7, ação")).toBe(
      "https://wa.me/5500900000001?text=Incidente%20%237%2C%20a%C3%A7%C3%A3o",
    );
  });
});

describe("incidentContactMessage", () => {
  it("identifies the incident by number, category and location", () => {
    expect(
      incidentContactMessage({ id: 7, category: "MECHANICAL_PROBLEM", location: "BR-116, km 230" }),
    ).toBe(
      "Olá! Aqui é a central Logos, sobre o incidente #7 (Problema Mecânico, BR-116, km 230).",
    );
  });
});
