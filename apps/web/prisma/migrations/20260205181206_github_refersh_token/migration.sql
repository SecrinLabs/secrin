/*
  Warnings:

  - A unique constraint covering the columns `[slug]` on the table `Project` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "GitHubInstallation" ADD COLUMN     "refreshToken" TEXT,
ADD COLUMN     "tokenExpiresAt" TIMESTAMP(3);

-- AlterTable
ALTER TABLE "Project" ADD COLUMN     "docGenStatus" TEXT,
ADD COLUMN     "githubOwner" TEXT,
ADD COLUMN     "lastDocGenAt" TIMESTAMP(3),
ADD COLUMN     "slug" TEXT,
ADD COLUMN     "sourceRepoBranch" TEXT,
ADD COLUMN     "sourceRepoName" TEXT,
ADD COLUMN     "sourceRepoOwner" TEXT,
ADD COLUMN     "sourceRepoUrl" TEXT,
ADD COLUMN     "webhookId" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "Project_slug_key" ON "Project"("slug");

-- CreateIndex
CREATE INDEX "Project_sourceRepoOwner_sourceRepoName_idx" ON "Project"("sourceRepoOwner", "sourceRepoName");
