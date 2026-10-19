import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    category: z.string(),
    tags: z.array(z.string()).optional(),
    thumbnail: z.string().optional(),
    featured: z.boolean().optional().default(false),
    draft: z.boolean().optional().default(false),
    affiliates: z.array(z.string()).optional(),
    pr: z.boolean().optional().default(false),
    articleType: z.enum(["diary", "leadgen", "review", "hub", "video"]).optional(),
    videoUrl: z.string().optional(),
    videoSeries: z.enum(["ひとりの夜", "ふたりの夜", "みんなの食卓"]).optional(),
  }),
});

export const collections = { blog };
