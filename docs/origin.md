# The Origin of This Project / 项目缘起

*Behind the code: the research and the people that shaped this work.*

This page preserves the personal story behind the project in full. The README carries only a short summary so the technical documentation stays concise; the original narrative lives here.

---

## English — "Why this project exists"

This project is an extension of the Neo4j-based property graph schema I designed during my master's studies.

Back then, my original goal was to develop a standardized schema for property graph models. I wanted to create a unified structure that could organize and manage unstructured, heterogeneous manufacturing tool data from different manufacturers, covering various types of cutting tools, products, materials, and machining processes, all under a consistent set of definitions and constraints.

Most of my work at that time involved collecting data from manufacturers, analyzing data structures, and identifying the relationships between different types of cutting tools, products, materials, and other related entities. By understanding and abstracting these relationships, I hoped to eventually establish a unified schema capable of representing all this information.

To be honest, much of that work was quite tedious.

Day after day, I searched for data, downloaded catalogs, went through technical documents, and organized information piece by piece. It was a process that required a great deal of patience and persistence.

What made it even more challenging was that I wasn't entirely sure what I was working toward. I didn't really know how meaningful my research would turn out to be, or how much practical value it could eventually create.

Looking back now, however, I realize that the most valuable thing I gained from that experience wasn't necessarily the technical outcome itself. It was the personal growth that came along with it.

That period taught me how to slow down, how to be more patient, and how to remain committed to something I genuinely believed was worth doing, even when the results were uncertain.

And I believe these lessons have become increasingly valuable in today's world.

We live in a time when AI technologies and countless new challenges are constantly transforming the world around us. Everything seems to be moving faster and faster, and the pressure to keep up with that pace only continues to grow.

As individuals, I believe it is becoming increasingly important to develop the ability to reduce the impact of these external pressures on ourselves.

Because thinking matters. And sometimes, slowing down matters just as much.

Thanks to those years of research, I developed a little more resilience and patience. When facing uncertainty, pressure, or unexpected challenges, I now find myself better able to pause, reflect, and approach problems with a calmer and more focused mindset.

I am especially grateful to my academic supervisor.

During my master's studies, he met with me one-on-one every week, patiently guiding me through the details of my research and helping me find the right direction.

But more importantly, he taught me something that has stayed with me ever since.

He once told me:

> "Good ideas and great designs don't simply appear in a sudden moment of inspiration. They emerge from countless days and nights of learning, thinking, and accumulating knowledge about technology, industry, and your own research interests. They are shaped by real work, practical experience, and the projects you have been through.
>
> Slow down. Take your time. Think deeply."

These words have stayed with me, and I believe they will continue to guide me throughout my life.

I would also like to take this opportunity to wish my supervisor a wonderful and fulfilling retirement!

The idea of restarting this project came to me quite suddenly.

One day, the research I had put aside since graduate school somehow resurfaced in my mind. I started thinking that perhaps the work I had done back then still had some value.

And after spending several years working in the industry, I have become increasingly convinced that data standardization and semantic alignment are becoming more important than ever in industrial applications. This is especially true in the age of AI: no matter how powerful AI models become, the quality of the underlying data fundamentally determines how well they can perform.

Industrial data, by its very nature, is highly heterogeneous. It comes from different manufacturers, systems, standards, and engineering practices. The same concept may be described in different ways, while similar terms may carry completely different meanings depending on the context.

Without a consistent semantic foundation, integrating, understanding, and effectively utilizing such data becomes extremely difficult. And that is exactly why I believe we need a standardized way to represent and organize industrial knowledge.

So I decided to revisit my original research, rethink some of the design decisions, and improve the architecture based on what I have learned since then. This project is the result of that process.

I have chosen to make it open source, hoping that the ideas, designs, and experiences shared here might be useful to others who are working on similar challenges. Whether you are a student exploring knowledge graphs, a researcher working on industrial knowledge representation, or an engineer trying to make sense of complex manufacturing data, I sincerely hope you can find something valuable in this project.

Thank you for everything.

---

## 简体中文 — 为什么会有这个项目

这个项目就是我研究生期间设计的基于Neo4j的属性图模型 schema 的基础之上的延申。当时的初衷主要是整理了一套面向属性图模型的schema，希望能够通过这样的一套schema，能够将非结构化的、不同厂家的、多种类型的生产加工刀具信息统一以一个标准属性图的结构和约束管理起来。这个期间的工作大多数是在收集厂商的数据，分析数据结构，寻找各种各样不同的刀具、产品、材料和逻辑关系等要素之间的关联，进而能够在这样的抽象关联基础之上做出一个统一的schema。

这个期间其实工作说白了蛮无聊的，就是搜数据，下载下来看一看，每天整理一些数据内容。这个过程还是很消耗心性的，因为不知道自己做的东西究竟有什么意义，也不知道这个东西究竟能够创造多大的价值。不过回头来看，这段经历带给我的更多是心态上的成长，这个很宝贵！自己拥有了能够让自己稍微慢下来的能力，也拥有了更加坚定的信心去坚持自己认为正确的事情。

尤其是在当前这个社会，被AI技术和各样新的挑战不断冲击情况下，变得越来越快，这个冲下去的动能越来越大。作为个体而言，能够在这样的环境下，尽可能降低环境对自己的冲击和影响就显得格外重要。

因为思考很重要，慢下来的节奏对于人生来讲也很重要。得益于这段时间的工作和经历，我能够稍微有一些心态上的坚韧性，能够在面对外部冲击的情况下，有一些能力去让自己慢下来，去思考，去沉下心面对问题和解决问题。在此特别向我的老师表示感谢，他每周都会和我一对一谈话，指导详细的工作内容和方向。

最重要的，他曾对我说，好的想法和设计并不是灵光一现就能够想出来的，是日日夜夜的对于技术、对于行业、对于自己的研究方向积累的基础之上，叠加着实际的工作经验和项目经验能够得到的，要慢下来，要认真思考。

这段话对我收益终生。祝愿我的老师退休生活快乐！~

这个项目的始发来源于我突然的想法，尘封的研究生工作从我大脑里给翻了出来。我觉得这份工作稍微有一些些价值。

同样，自己工作了一段时间之后，越发认为在工业领域中，数据的标准化和语义对齐越来越重要，尤其是在AI盛行的今天，高质量的数据从根本上决定了AI的性能。并且，工业领域的数据天然就是异构并且语义混乱的，需要一套标准，所以我把自己的经验和设计稍微优化了一下，开源出来，希望能够帮到每一个看到了、搜索到了这个项目的人。